import os

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential


PERSON_CONFIDENCE_THRESHOLD = 0.5
PERSON_NMS_IOU_THRESHOLD = 0.5

# 사람이 없을 때도 개인 물건이 감지되면 "잠깐 자리를 비운 상태"일 수 있습니다.
# Azure Object Detection 태그는 모델/이미지에 따라 대소문자나 표현이 조금씩 달라질 수 있어
# 소문자 부분 문자열 기준으로 판단합니다.
PERSONAL_OBJECT_KEYWORDS = {
    "laptop",
    "backpack",
    "bag",
    "bags",
    "book",
    "chair",
    "table",
    "luggage",
}


def normalize_bounding_box(bounding_box):
    """Azure SDK bounding_box 값을 {'x', 'y', 'w', 'h'} dict 형태로 통일합니다."""
    if isinstance(bounding_box, dict):
        return {
            "x": int(bounding_box["x"]),
            "y": int(bounding_box["y"]),
            "w": int(bounding_box["w"]),
            "h": int(bounding_box["h"]),
        }

    # SDK 버전에 따라 dict가 아닌 ImageBoundingBox 모델 객체로 반환됩니다.
    # 출력 repr은 {'x', 'y', 'w', 'h'}처럼 보일 수 있지만, 실제 속성명은
    # 버전에 따라 width/height 또는 w/h로 다를 수 있어 둘 다 처리합니다.
    width = getattr(bounding_box, "w", None)
    if width is None:
        width = getattr(bounding_box, "width")

    height = getattr(bounding_box, "h", None)
    if height is None:
        height = getattr(bounding_box, "height")

    return {
        "x": int(bounding_box.x),
        "y": int(bounding_box.y),
        "w": int(width),
        "h": int(height),
    }


def calculate_iou(box_a, box_b):
    """두 bounding box의 IoU(Intersection over Union)를 계산합니다."""
    a = normalize_bounding_box(box_a)
    b = normalize_bounding_box(box_b)

    a_x2 = a["x"] + a["w"]
    a_y2 = a["y"] + a["h"]
    b_x2 = b["x"] + b["w"]
    b_y2 = b["y"] + b["h"]

    intersection_x1 = max(a["x"], b["x"])
    intersection_y1 = max(a["y"], b["y"])
    intersection_x2 = min(a_x2, b_x2)
    intersection_y2 = min(a_y2, b_y2)

    intersection_width = max(0, intersection_x2 - intersection_x1)
    intersection_height = max(0, intersection_y2 - intersection_y1)
    intersection_area = intersection_width * intersection_height

    area_a = a["w"] * a["h"]
    area_b = b["w"] * b["h"]
    union_area = area_a + area_b - intersection_area

    if union_area == 0:
        return 0.0

    return intersection_area / union_area


def filter_people_detections(
    people,
    confidence_threshold=PERSON_CONFIDENCE_THRESHOLD,
    iou_threshold=PERSON_NMS_IOU_THRESHOLD,
):
    """
    People Detection 결과를 confidence threshold와 IoU 기반 NMS로 후처리합니다.

    개인정보 보호를 위해 얼굴 인식이나 개인 식별은 수행하지 않습니다.
    이 코드는 사람 수와 객체 존재 여부만 판단합니다.
    """
    if people is None:
        return []

    # 1. confidence가 낮은 false positive 후보를 먼저 제거합니다.
    confident_people = [
        person
        for person in people
        if person.confidence is not None and person.confidence >= confidence_threshold
    ]

    # 2. confidence가 높은 detection을 우선 남기기 위해 내림차순 정렬합니다.
    sorted_people = sorted(
        confident_people,
        key=lambda person: person.confidence,
        reverse=True,
    )

    # 3. 이미 선택된 bbox와 크게 겹치는 detection은 중복으로 보고 제거합니다.
    selected_people = []
    for candidate in sorted_people:
        is_duplicate = any(
            calculate_iou(candidate.bounding_box, selected.bounding_box) >= iou_threshold
            for selected in selected_people
        )

        if not is_duplicate:
            selected_people.append(candidate)

    return selected_people


def get_object_name_and_confidence(detected_object):
    """Azure Object Detection 결과에서 대표 tag 이름과 confidence를 꺼냅니다."""
    if not detected_object.tags:
        return None, None

    primary_tag = detected_object.tags[0]
    return primary_tag.name, primary_tag.confidence


def is_personal_object(object_name):
    """객체명이 개인 물건/좌석 관련 키워드를 포함하는지 확인합니다."""
    if object_name is None:
        return False

    normalized_name = object_name.lower()
    return any(keyword in normalized_name for keyword in PERSONAL_OBJECT_KEYWORDS)


def filter_relevant_objects(objects):
    """방 상태 판단에 사용할 주요 객체만 추려냅니다."""
    if objects is None:
        return []

    relevant_objects = []
    for detected_object in objects:
        object_name, confidence = get_object_name_and_confidence(detected_object)
        if is_personal_object(object_name):
            relevant_objects.append(
                {
                    "name": object_name,
                    "confidence": confidence,
                    "bounding_box": normalize_bounding_box(detected_object.bounding_box),
                }
            )

    return relevant_objects


def decide_room_status(people_count, relevant_objects):
    """필터링된 사람 수와 개인 물건 감지 여부로 최종 방 상태를 판단합니다."""
    if people_count >= 1:
        return "사용 중"

    if relevant_objects:
        return "일시 자리 비움 가능성"

    return "비어 있음"


def print_filtered_people(filtered_people):
    print("Filtered People:")

    if not filtered_people:
        print("  No people detected after filtering.")
        return

    for index, person in enumerate(filtered_people, start=1):
        bbox = normalize_bounding_box(person.bounding_box)
        print(f"  Person {index}: bbox={bbox}, confidence={person.confidence:.4f}")


def print_detected_objects(relevant_objects):
    print("Detected objects:")

    if not relevant_objects:
        print("  No relevant objects detected.")
        return

    for detected_object in relevant_objects:
        print(
            f"  {detected_object['name']}: "
            f"bbox={detected_object['bounding_box']}, "
            f"confidence={detected_object['confidence']:.4f}"
        )


def main():
    # Set the values of your computer vision endpoint and computer vision key
    # as environment variables:
    try:
        endpoint = os.environ["VISION_ENDPOINT"]
        key = os.environ["VISION_KEY"]
    except KeyError:
        print("Missing environment variable 'VISION_ENDPOINT' or 'VISION_KEY'")
        print("Set them before running this sample.")
        exit()

    # Create an Image Analysis client
    client = ImageAnalysisClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
    )

    # Load local image as bytes
    with open("teamroom.jpg", "rb") as f:
        image_data = f.read()

    # 기존 Azure Vision SDK 호출 코드는 유지합니다.
    result = client.analyze(
        image_data=image_data,
        visual_features=[VisualFeatures.PEOPLE, VisualFeatures.OBJECTS],
    )

    print("Image analysis results:")

    # 원본 Objects 결과도 확인할 수 있도록 출력합니다.
    if result.objects is not None:
        print("Objects:")
        for detected_object in result.objects.list:
            object_name, confidence = get_object_name_and_confidence(detected_object)
            print(
                f"  {object_name}, {detected_object.bounding_box}, "
                f"Confidence: {confidence:.4f}"
            )

    # 원본 People 결과도 확인할 수 있도록 출력합니다.
    if result.people is not None:
        print("People:")
        for person in result.people.list:
            print(f"  {person.bounding_box}, Confidence {person.confidence:.4f}")

    filtered_people = filter_people_detections(
        result.people.list if result.people is not None else [],
        confidence_threshold=PERSON_CONFIDENCE_THRESHOLD,
        iou_threshold=PERSON_NMS_IOU_THRESHOLD,
    )
    relevant_objects = filter_relevant_objects(
        result.objects.list if result.objects is not None else []
    )
    people_count = len(filtered_people)
    room_status = decide_room_status(people_count, relevant_objects)

    print()
    print_filtered_people(filtered_people)

    print()
    print_detected_objects(relevant_objects)

    print()
    print("Final room status:")
    print(f"  People count: {people_count}")
    print(f"  Status: {room_status}")

    if result.metadata is not None:
        print()
        print(f"Image height: {result.metadata.height}")
        print(f"Image width: {result.metadata.width}")
    print(f"Model version: {result.model_version}")


if __name__ == "__main__":
    main()
