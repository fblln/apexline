from __future__ import annotations

import math

from .models import DirectLineStats, FitStats, LapNormalization, LatLon, ScoredFastF1Lap, SimplificationStats, XY


def projection_origin(points: list[LatLon]) -> LatLon:
    return (
        sum(lat for lat, _ in points) / len(points),
        sum(lon for _, lon in points) / len(points),
    )


def latlon_to_xy(point: LatLon, origin: LatLon) -> XY:
    lat, lon = point
    origin_lat, origin_lon = origin
    radius_m = 6_371_000.0
    cos_origin = math.cos(math.radians(origin_lat))
    return (
        math.radians(lon - origin_lon) * radius_m * cos_origin,
        math.radians(lat - origin_lat) * radius_m,
    )


def xy_to_latlon(point: XY, origin: LatLon) -> LatLon:
    x, y = point
    origin_lat, origin_lon = origin
    radius_m = 6_371_000.0
    cos_origin = math.cos(math.radians(origin_lat))
    return (
        math.degrees(y / radius_m) + origin_lat,
        math.degrees(x / (radius_m * cos_origin)) + origin_lon,
    )


def path_length(points: list[XY]) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))


def cumulative_lengths(points: list[XY]) -> list[float]:
    distances = [0.0]
    total = 0.0
    for a, b in zip(points, points[1:]):
        total += math.hypot(b[0] - a[0], b[1] - a[1])
        distances.append(total)
    return distances


def point_at_distance(points: list[XY], distances: list[float], target: float) -> XY:
    if target <= 0.0:
        return points[0]
    if target >= distances[-1]:
        return points[-1]

    low = 0
    high = len(distances) - 1
    while low < high:
        mid = (low + high) // 2
        if distances[mid] < target:
            low = mid + 1
        else:
            high = mid

    right = max(1, low)
    left = right - 1
    segment_length = max(distances[right] - distances[left], 1e-9)
    t = (target - distances[left]) / segment_length
    ax, ay = points[left]
    bx, by = points[right]
    return (ax + t * (bx - ax), ay + t * (by - ay))


def slice_polyline_by_distance(points: list[XY], distances: list[float], start: float, end: float) -> list[XY]:
    if start >= end:
        return []

    sliced = [point_at_distance(points, distances, start)]
    for point, distance in zip(points, distances):
        if start < distance < end:
            if point != sliced[-1]:
                sliced.append(point)
    end_point = point_at_distance(points, distances, end)
    if end_point != sliced[-1]:
        sliced.append(end_point)
    return sliced


def normalize_repeated_lap_segment(
    points: list[XY],
    *,
    target_length_m: float,
    scale_m_per_unit: float = 0.1,
    length_tolerance_pct: float = 0.05,
    min_points: int = 4,
    max_endpoint_gap_m: float | None = None,
) -> tuple[list[XY], LapNormalization] | None:
    """Trim a repeated overlap from an over-long FastF1 lap trace.

    FastF1 lap boundaries can occasionally include a short segment twice. This
    finds a contiguous one-lap window whose length matches the oracle circuit
    and whose start/end close like a lap, without warping the shape.
    """

    if len(points) < min_points or target_length_m <= 0.0 or scale_m_per_unit <= 0.0:
        return None

    distances = cumulative_lengths(points)
    total_units = distances[-1]
    total_m = total_units * scale_m_per_unit
    if total_m < target_length_m:
        return None

    target_units = target_length_m / scale_m_per_unit
    endpoint_limit_m = max_endpoint_gap_m if max_endpoint_gap_m is not None else max(25.0, target_length_m * 0.015)
    best: tuple[float, list[XY], LapNormalization] | None = None

    candidate_starts = sorted(
        {
            start
            for start in [*distances[:-1], *(distance - target_units for distance in distances[1:])]
            if 0.0 <= start and start + target_units <= total_units
        }
    )

    for start in candidate_starts:
        end = start + target_units

        candidate = slice_polyline_by_distance(points, distances, start, end)
        if len(candidate) < min_points:
            continue

        endpoint_gap_m = math.hypot(candidate[-1][0] - candidate[0][0], candidate[-1][1] - candidate[0][1]) * scale_m_per_unit
        normalized_length_m = path_length(closed_path(candidate)) * scale_m_per_unit
        length_error_pct = abs(normalized_length_m - target_length_m) / target_length_m
        if endpoint_gap_m > endpoint_limit_m or length_error_pct > length_tolerance_pct:
            continue

        normalization = LapNormalization(
            original_points=len(points),
            normalized_points=len(candidate),
            original_path_length_m=path_length(closed_path(points)) * scale_m_per_unit,
            normalized_path_length_m=normalized_length_m,
            target_length_m=target_length_m,
            trimmed_prefix_m=start * scale_m_per_unit,
            trimmed_suffix_m=(total_units - end) * scale_m_per_unit,
            endpoint_gap_m=endpoint_gap_m,
        )
        score = endpoint_gap_m + abs(normalized_length_m - target_length_m)
        if best is None or score < best[0]:
            best = (score, candidate, normalization)

    if best is None:
        return None
    return best[1], best[2]


def without_duplicate_closure(points: list[XY]) -> list[XY]:
    if len(points) >= 2 and points[0] == points[-1]:
        return points[:-1]
    return points


def closed_path(points: list[XY]) -> list[XY]:
    points = without_duplicate_closure(points)
    return points if points[-1] == points[0] else points + [points[0]]


def resample_closed(points: list[XY], sample_count: int) -> list[XY]:
    loop = closed_path(points)
    distances = [0.0]
    total = 0.0
    for a, b in zip(loop, loop[1:]):
        total += math.hypot(b[0] - a[0], b[1] - a[1])
        distances.append(total)

    sampled: list[XY] = []
    segment_index = 0
    for i in range(sample_count):
        target = total * i / sample_count
        while segment_index < len(distances) - 2 and distances[segment_index + 1] < target:
            segment_index += 1

        segment_length = max(distances[segment_index + 1] - distances[segment_index], 1e-9)
        t = (target - distances[segment_index]) / segment_length
        ax, ay = loop[segment_index]
        bx, by = loop[segment_index + 1]
        sampled.append((ax + t * (bx - ax), ay + t * (by - ay)))

    return sampled


def rotate_samples(points: list[XY], offset: int) -> list[XY]:
    offset %= len(points)
    return points[offset:] + points[:offset]


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = (len(sorted_values) - 1) * pct / 100
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return sorted_values[int(index)]
    fraction = index - low
    return sorted_values[low] * (1 - fraction) + sorted_values[high] * fraction


def similarity_fit(source: list[XY], target: list[XY]) -> FitStats:
    source_complex = [complex(x, y) for x, y in source]
    target_complex = [complex(x, y) for x, y in target]
    source_mean = sum(source_complex) / len(source_complex)
    target_mean = sum(target_complex) / len(target_complex)
    centered_source = [point - source_mean for point in source_complex]
    centered_target = [point - target_mean for point in target_complex]
    covariance = sum(t * s.conjugate() for s, t in zip(centered_source, centered_target))
    denominator = sum(abs(point) ** 2 for point in centered_source)
    coefficient = covariance / denominator
    transformed = [coefficient * point + target_mean - coefficient * source_mean for point in source_complex]
    errors = [abs(t - s) for t, s in zip(target_complex, transformed)]
    angle = math.degrees(math.atan2(coefficient.imag, coefficient.real))
    return FitStats(
        direction="forward",
        start_offset_samples=0,
        sample_count=len(source),
        rmse_m=math.sqrt(sum(error * error for error in errors) / len(errors)),
        p50_m=percentile(errors, 50),
        p95_m=percentile(errors, 95),
        max_m=max(errors),
        scale_m_per_fastf1_unit=abs(coefficient),
        rotation_degrees=angle,
    )


def validate_shape(
    fastf1_xy: list[XY],
    gps_xy: list[XY],
    sample_count: int,
    offset_step: int,
) -> FitStats:
    source = resample_closed(fastf1_xy, sample_count)
    target = resample_closed(gps_xy, sample_count)
    coarse_offsets = range(0, sample_count, max(offset_step, 1))
    best: FitStats | None = None

    for direction, target_points in (
        ("forward", target),
        ("reversed", list(reversed(target))),
    ):
        best_coarse_offset = 0
        best_coarse_rmse = float("inf")
        for offset in coarse_offsets:
            coarse_fit = similarity_fit(source, rotate_samples(target_points, offset))
            if coarse_fit.rmse_m < best_coarse_rmse:
                best_coarse_rmse = coarse_fit.rmse_m
                best_coarse_offset = offset

        offset_start = max(0, best_coarse_offset - max(offset_step - 1, 0))
        offset_end = min(sample_count, best_coarse_offset + max(offset_step, 1))
        for offset in range(offset_start, offset_end):
            fit = similarity_fit(source, rotate_samples(target_points, offset))
            fit = FitStats(
                direction=direction,
                start_offset_samples=offset,
                sample_count=fit.sample_count,
                rmse_m=fit.rmse_m,
                p50_m=fit.p50_m,
                p95_m=fit.p95_m,
                max_m=fit.max_m,
                scale_m_per_fastf1_unit=fit.scale_m_per_fastf1_unit,
                rotation_degrees=fit.rotation_degrees,
            )
            if best is None or fit.rmse_m < best.rmse_m:
                best = fit

    if best is None:
        raise RuntimeError("shape validation failed to evaluate any offsets")
    return best


def fit_aligned_samples(lap_points: list[XY], gps_xy: list[XY], fit: FitStats, sample_count: int) -> list[XY]:
    source = resample_closed(lap_points, sample_count)
    target = resample_closed(gps_xy, sample_count)
    target_for_fit = list(reversed(target)) if fit.direction == "reversed" else target
    target_for_fit = rotate_samples(target_for_fit, fit.start_offset_samples)

    source_complex = [complex(x, y) for x, y in source]
    target_complex = [complex(x, y) for x, y in target_for_fit]
    source_mean = sum(source_complex) / len(source_complex)
    target_mean = sum(target_complex) / len(target_complex)
    centered_source = [point - source_mean for point in source_complex]
    centered_target = [point - target_mean for point in target_complex]
    coefficient = sum(t * s.conjugate() for s, t in zip(centered_source, centered_target)) / sum(
        abs(point) ** 2 for point in centered_source
    )
    translation = target_mean - coefficient * source_mean
    transformed = [coefficient * point + translation for point in source_complex]
    aligned = [(point.real, point.imag) for point in transformed]
    aligned = rotate_samples(aligned, -fit.start_offset_samples)
    if fit.direction == "reversed":
        aligned = list(reversed(aligned))
    return aligned


def average_fitted_laps(scored_laps: list[ScoredFastF1Lap], gps_xy: list[XY], sample_count: int) -> list[XY]:
    fitted_lines = [
        fit_aligned_samples(item.lap.points, gps_xy, item.fit, sample_count)
        for item in scored_laps
    ]
    averaged: list[XY] = []
    for points_at_progress in zip(*fitted_lines):
        averaged.append(
            (
                sum(point[0] for point in points_at_progress) / len(points_at_progress),
                sum(point[1] for point in points_at_progress) / len(points_at_progress),
            )
        )
    return averaged


def direct_line_stats(a_xy: list[XY], b_xy: list[XY], sample_count: int) -> DirectLineStats:
    a = resample_closed(a_xy, sample_count)
    b = resample_closed(b_xy, sample_count)
    distances = [math.hypot(ax - bx, ay - by) for (ax, ay), (bx, by) in zip(a, b)]
    return DirectLineStats(
        sample_count=sample_count,
        rmse_m=math.sqrt(sum(distance * distance for distance in distances) / len(distances)),
        p50_m=percentile(distances, 50),
        p95_m=percentile(distances, 95),
        max_m=max(distances),
    )


def perpendicular_distance(point: XY, start: XY, end: XY) -> float:
    if start == end:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    px, py = point
    ax, ay = start
    bx, by = end
    dx = bx - ax
    dy = by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    closest = (ax + t * dx, ay + t * dy)
    return math.hypot(px - closest[0], py - closest[1])


def rdp(points: list[XY], tolerance_m: float) -> list[XY]:
    if len(points) <= 2:
        return points

    max_distance = -1.0
    split_index = -1
    for index in range(1, len(points) - 1):
        distance = perpendicular_distance(points[index], points[0], points[-1])
        if distance > max_distance:
            max_distance = distance
            split_index = index

    if max_distance <= tolerance_m:
        return [points[0], points[-1]]

    left = rdp(points[: split_index + 1], tolerance_m)
    right = rdp(points[split_index:], tolerance_m)
    return left[:-1] + right


def distance_to_polyline(point: XY, polyline: list[XY]) -> float:
    return min(
        perpendicular_distance(point, start, end)
        for start, end in zip(polyline, polyline[1:])
    )


def simplification_stats(source_xy: list[XY], simplified_xy: list[XY], tolerance_m: float, encoded: str) -> SimplificationStats:
    distances = [distance_to_polyline(point, simplified_xy) for point in source_xy]
    source_length_m = path_length(source_xy)
    simplified_length_m = path_length(simplified_xy)
    length_delta_m = simplified_length_m - source_length_m
    return SimplificationStats(
        source_points=len(source_xy),
        simplified_points=len(simplified_xy),
        encoded_chars=len(encoded),
        tolerance_m=tolerance_m,
        rmse_m=math.sqrt(sum(distance * distance for distance in distances) / len(distances)),
        p95_m=percentile(distances, 95),
        max_m=max(distances),
        source_length_m=source_length_m,
        simplified_length_m=simplified_length_m,
        length_delta_m=length_delta_m,
        length_delta_pct=(length_delta_m / source_length_m * 100) if source_length_m else 0.0,
    )


def encode_signed(value: int) -> str:
    value = ~(value << 1) if value < 0 else value << 1
    chunks: list[str] = []
    while value >= 0x20:
        chunks.append(chr((0x20 | (value & 0x1F)) + 63))
        value >>= 5
    chunks.append(chr(value + 63))
    return "".join(chunks)


def encode_polyline(points: list[LatLon], precision: int) -> str:
    factor = 10**precision
    last_lat = 0
    last_lon = 0
    output: list[str] = []
    for lat, lon in points:
        encoded_lat = int(round(lat * factor))
        encoded_lon = int(round(lon * factor))
        output.append(encode_signed(encoded_lat - last_lat))
        output.append(encode_signed(encoded_lon - last_lon))
        last_lat = encoded_lat
        last_lon = encoded_lon
    return "".join(output)
