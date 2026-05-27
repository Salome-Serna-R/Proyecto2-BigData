import csv
import io
import json
import os
from collections import defaultdict

import boto3


s3 = boto3.client("s3")

BUCKET_NAME = os.environ.get("BUCKET_NAME")
PLACES_KEY = os.environ.get("PLACES_KEY", "trusted/places_clean.csv")
TYPES_KEY = os.environ.get("TYPES_KEY", "trusted/place_types_clean.csv")
HOURS_KEY = os.environ.get("HOURS_KEY", "trusted/place_hours_clean.csv")


def json_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def read_csv_from_s3(key):
    if not BUCKET_NAME:
        raise ValueError("Missing BUCKET_NAME environment variable")

    obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
    content = obj["Body"].read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(content)))


def to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def to_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def to_bool(value):
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    return normalized in ["true", "1", "yes", "y", "si", "sí"]


def normalize_place(row):
    return {
        "place_id": row.get("place_id", ""),
        "name": row.get("name", ""),
        "address": row.get("address", ""),
        "neighborhood": row.get("neighborhood", ""),
        "lat": to_float(row.get("lat")),
        "lng": to_float(row.get("lng")),
        "rating": to_float(row.get("rating")),
        "price_level": to_int(row.get("price_level")),
        "review_count": to_int(row.get("review_count")),
    }


def load_data():
    places_raw = read_csv_from_s3(PLACES_KEY)
    types_raw = read_csv_from_s3(TYPES_KEY)
    hours_raw = read_csv_from_s3(HOURS_KEY)

    places = [normalize_place(row) for row in places_raw]

    types_by_place = defaultdict(list)
    for row in types_raw:
        place_id = row.get("place_id", "")
        place_type = row.get("type", "")
        if place_id and place_type:
            types_by_place[place_id].append(place_type)

    open_days_by_place = defaultdict(int)
    weekend_open_by_place = defaultdict(int)

    for row in hours_raw:
        place_id = row.get("place_id", "")
        day_en = row.get("day_en", "")
        is_open = to_bool(row.get("is_open"))

        if not place_id or not is_open:
            continue

        open_days_by_place[place_id] += 1

        if day_en in ["Saturday", "Sunday"]:
            weekend_open_by_place[place_id] += 1

    enriched = []

    for place in places:
        place_id = place["place_id"]
        place_types = types_by_place.get(place_id, [])

        enriched.append({
            **place,
            "types": place_types,
            "primary_type": place_types[0] if place_types else None,
            "open_days_count": open_days_by_place.get(place_id, 0),
            "opens_on_weekend": weekend_open_by_place.get(place_id, 0) > 0,
        })

    return enriched


def apply_filters(records, params):
    filtered = records

    neighborhood = params.get("neighborhood")
    place_type = params.get("type")
    min_rating = params.get("min_rating")
    weekend = params.get("weekend")

    if neighborhood:
        filtered = [
            item for item in filtered
            if item.get("neighborhood", "").lower() == neighborhood.lower()
        ]

    if place_type:
        filtered = [
            item for item in filtered
            if place_type.lower() in [t.lower() for t in item.get("types", [])]
        ]

    if min_rating:
        min_rating_number = to_float(min_rating)
        filtered = [
            item for item in filtered
            if item.get("rating", 0) >= min_rating_number
        ]

    if weekend is not None:
        weekend_bool = to_bool(weekend)
        filtered = [
            item for item in filtered
            if item.get("opens_on_weekend") == weekend_bool
        ]

    return filtered


def build_summary(records):
    total_records = len(records)
    total_reviews = sum(item.get("review_count", 0) for item in records)

    if total_records == 0:
        return {
            "records": 0,
            "average_rating": 0,
            "total_reviews": 0,
            "average_price_level": 0,
        }

    ratings = [item.get("rating", 0) for item in records if item.get("rating", 0) > 0]
    prices = [item.get("price_level", 0) for item in records if item.get("price_level", 0) > 0]

    return {
        "records": total_records,
        "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
        "total_reviews": total_reviews,
        "average_price_level": round(sum(prices) / len(prices), 2) if prices else 0,
    }


def by_neighborhood(records, limit=10):
    grouped = defaultdict(lambda: {
        "neighborhood": "",
        "places_count": 0,
        "rating_sum": 0,
        "rating_count": 0,
        "total_reviews": 0,
    })

    for item in records:
        neighborhood = item.get("neighborhood") or "Unknown"
        grouped[neighborhood]["neighborhood"] = neighborhood
        grouped[neighborhood]["places_count"] += 1
        grouped[neighborhood]["total_reviews"] += item.get("review_count", 0)

        if item.get("rating", 0) > 0:
            grouped[neighborhood]["rating_sum"] += item.get("rating", 0)
            grouped[neighborhood]["rating_count"] += 1

    result = []
    for item in grouped.values():
        rating_count = item.pop("rating_count")
        rating_sum = item.pop("rating_sum")
        item["average_rating"] = round(rating_sum / rating_count, 2) if rating_count else 0
        result.append(item)

    return sorted(result, key=lambda x: x["places_count"], reverse=True)[:limit]


def by_type(records, limit=10):
    grouped = defaultdict(lambda: {
        "type": "",
        "places_count": 0,
        "rating_sum": 0,
        "rating_count": 0,
        "total_reviews": 0,
    })

    for item in records:
        for place_type in item.get("types", []):
            grouped[place_type]["type"] = place_type
            grouped[place_type]["places_count"] += 1
            grouped[place_type]["total_reviews"] += item.get("review_count", 0)

            if item.get("rating", 0) > 0:
                grouped[place_type]["rating_sum"] += item.get("rating", 0)
                grouped[place_type]["rating_count"] += 1

    result = []
    for item in grouped.values():
        rating_count = item.pop("rating_count")
        rating_sum = item.pop("rating_sum")
        item["average_rating"] = round(rating_sum / rating_count, 2) if rating_count else 0
        result.append(item)

    return sorted(result, key=lambda x: x["places_count"], reverse=True)[:limit]


def lambda_handler(event, context):
    try:
        path = event.get("rawPath") or event.get("path") or "/summary"
        params = event.get("queryStringParameters") or {}

        records = load_data()
        filtered = apply_filters(records, params)

        limit = to_int(params.get("limit", 10), 10)

        if path.endswith("/summary"):
            return json_response(200, {
                "filters": params,
                **build_summary(filtered),
                "available_endpoints": [
                    "/summary",
                    "/by-neighborhood",
                    "/by-type",
                    "/records",
                ],
            })

        if path.endswith("/by-neighborhood"):
            return json_response(200, {
                "filters": params,
                "items": by_neighborhood(filtered, limit),
            })

        if path.endswith("/by-type"):
            return json_response(200, {
                "filters": params,
                "items": by_type(filtered, limit),
            })

        if path.endswith("/records"):
            return json_response(200, {
                "filters": params,
                "count": len(filtered),
                "items": filtered[:limit],
            })

        return json_response(404, {
            "message": "Endpoint not found",
            "path": path,
            "available_endpoints": [
                "/summary",
                "/by-neighborhood",
                "/by-type",
                "/records",
            ],
        })

    except Exception as error:
        return json_response(500, {
            "message": "Internal server error",
            "error": str(error),
        })