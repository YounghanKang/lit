# LIT 5월 정기발표

# Azure Vision으로 공간 예약 시스템에 ‘눈’을 달다

예약 정보와 실제 사용 상태의 불일치를 AI Vision으로 해결하기

# 서론

## 오프닝

여러분은 도서관 팀플룸이나 좌석을 예약하려고 했는데, 앱에서는 이미 예약이 꽉 차 있어서 포기한 경험이 있으신가요?

그런데 막상 지나가다 보면 예약된 시간인데도 방이 비어 있거나, 반대로 퇴실 처리가 되었는데도 사람들이 계속 사용하고 있는 경우를 본 적이 있을 것입니다.

이 문제는 단순히 “예약자의 비매너”만의 문제가 아닙니다. 더 근본적인 문제는 현재의 예약 시스템이 실제 공간의 상태를 알지 못한다는 데 있습니다.

현재 대부분의 예약 시스템은 사용자가 입력한 정보와 버튼 클릭에 의존합니다. 누가 예약했는지, 몇 시부터 몇 시까지 예약했는지, 입실이나 퇴실 버튼을 눌렀는지는 알 수 있습니다. 하지만 실제로 사람이 들어왔는지, 예약 시간 동안 계속 사용하고 있는지, 퇴실 처리 후에도 자리를 점유하고 있는지는 알기 어렵습니다.

| 시스템이 아는 것 | 시스템이 모르는 것 |
| --- | --- |
| 누가 예약했는지 | 실제로 입실했는지 |
| 몇 시부터 몇 시까지 예약했는지 | 예약 시간 동안 계속 사용 중인지 |
| 퇴실 버튼을 눌렀는지 | 퇴실 후에도 자리를 점유 중인지 |
| 예약 가능/불가능 상태 | 현실 공간의 실제 점유 상태 |

즉, 현재 예약 시스템은 “예약 정보”는 관리하지만, “실제 공간 사용 상태”는 확인하지 못합니다.

이번 발표에서는 도서관 예약 시스템을 예시로 들어 이 문제를 Azure AI Vision을 활용해 해결하는 방법을 소개하려고 합니다. 핵심 아이디어는 간단합니다.

> 예약 시스템에 현실 공간을 볼 수 있는 ‘눈’을 달아주는 것입니다.
> 

Azure AI Vision을 이용해 공간 이미지에서 사람의 존재 여부와 객체 정보를 분석하고, 이 결과를 예약 데이터와 비교하면 예약 정보와 실제 사용 상태가 어긋나는 상황을 감지할 수 있습니다.

## 문제 정의

저희가 이용하는 도서관 예약 시스템에는 크게 세가지의 허점이 있습니다. 

### **문제 1. 예약은 되었지만 실제로 사용하지 않는 경우**

첫 번째 문제는 예약만 해두고 실제로 공간을 사용하지 않는 경우입니다.

사용자가 예약만 해두고 입실하지 않거나, GPS 기반 입실만 누르고 실제로 방을 사용하지 않는 경우가 있습니다. 

### **문제 2. 일찍 끝났지만 퇴실 처리를 하지 않는 경우**

두 번째 문제는 사용이 일찍 끝났지만 퇴실 처리를 하지 않는 경우입니다.

만약, 팀플이나 할일이 일찍 끝나서 예약해놓은 방이 비게 되더라도, 퇴실처리를 하지 않으면, 남은 시간 동안 그 방은 계속 예약 중으로 표시되게 됩니다.

또, 현재 30분 단위로 예약이 가능한 현재 시스템상 이러한 방식은 공간의 사용이 매우 비효율적으로 이루어지고 있다는 점을 시사합니다. 

### **문제 3. 퇴실 처리 후에도 자리를 계속 차지하는 경우**

세 번째 문제는 반대로 퇴실 처리를 해놓고도 계속 공간을 사용하는 경우입니다.

사용자가 점유할 수 있는 시간이 지났지만 이를 연장하지 않아서, 실제로는 팀플룸 안에 계속 머물 수 있습니다. 이때 시스템은 해당 공간을 비어 있다고 판단하고 다음 예약을 받을 수 있습니다.

그러면 다음 예약자는 예약 시간에 도착했지만 공간을 바로 사용할 수 없는 문제가 발생합니다.

다음 예약자는 예약했는데도 바로 이용하지 못하는 문제가 발생하는 것이죠.

### 이 세 가지 문제의 공통점은 하나입니다.

> **예약 데이터와 실제 공간 상태가 일치하지 않는다는 것입니다.**
> 

# 본론

그렇다면 이러한 문제를 어떻게 해결 할 수 있을까요?

여기에 실제 공간 상태 데이터를 추가하면 시스템은 더 정확한 판단을 할 수 있습니다.

저희는 이 실제 공간 상태 데이터를 받는 방법으로 Azure AI Vision을 추천합니다.

## Azure AI Vision 소개

Azure AI Vision은 Microsoft Azure에서 제공하는 클라우드 기반 컴퓨터 비전 서비스입니다. 이미지를 분석해 텍스트, 객체, 사람, 태그, 캡션 등 다양한 시각 정보를 추출할 수 있습니다.

이번 발표에서는 그중에서도 특히 Azure AI Vision의 소분야인 Image Analysis의 People Detection과 Object Detection을 중심으로 사용합니다.

People Detection :  이미지 안에 나타난 사람을 감지하고, 각 사람의 위치를 bounding box 좌표와 confidence score로 반환합니다.

bounding box : 이미지 안에서 사람이 어디에 있는지를 표시하는 사각형 영역. 영역을 x, y, width, height 값으로 반환함.

![image.png](LIT%205%EC%9B%94%20%EC%A0%95%EA%B8%B0%EB%B0%9C%ED%91%9C/image.png)

confidence score : AI가 감지 결과를 얼마나 확신하는지 나타내는 신뢰도 점수
예 : Perple Detection 에서 confidence가 0.94이다? 그러면 94% 정도로 사람이 있음을 확신하는 거임.

Object DEtection : 이미지 안의 사물이나 물체를 감지하는 기능입니다. 

이번 발표에서는 사람 감지만으로 판단하지 않고, 노트북, 가방, 책, 의자, 테이블 같은 객체도 함께 확인합니다. 
왜냐하면 사람이 잠깐 자리를 비운 경우에는 사람은 감지되지 않지만 개인 물건은 남아 있을 수 있기 때문입니다. 이 경우 바로 “비어 있음”으로 판단하면 문제가 생길 수 있습니다. 
따라서 사람 감지 결과와 객체 감지 결과를 함께 사용해 공간 상태를 세밀하게 판단합니다.

그럼 여기서 의문이 드실 수도 있습니다. Vision 모델 그럼 그냥 만들어서 사용하면 되는거 아닌가? 왜 굳이Azure AI Visioin을 사용하는거지?

## **Azure AI Vision을 쓰는 이유**

## 왜 직접 모델을 만들지 않고 Azure AI Vision을 쓰는가?

사람 감지 시스템을 직접 만들려면 일반적으로 다음 과정이 필요합니다.

1. 공간 이미지 데이터 수집
2. 사람 위치 라벨링
3. 객체 탐지 모델 학습
4. 성능 평가
5. 모델 배포
6. 운영 중 재학습 및 유지보수

하지만 우리는 사람 감지 모델 자체를 연구하는 것이 아닙니다.

목적은 기존 예약 시스템에 실제 공간 상태 데이터를 연결하는 서비스 구조를 설계하는 것입니다.

따라서 Azure AI Vision을 사용하면 모델 학습 과정보다 서비스 로직, 데이터 흐름, 시스템 설계에 집중할 수 있습니다.

정리해보자면 Azure AI Vision을 통한 이 시스템은 아래와 같은 장점들이 있습니다. 

## 1. 빠른 프로토 타입 제작. + 서비스 구조 설계에 집중 가능

Azure AI Vision은  Azure 서버에 요청을 보내는 REST API와 그걸 파이썬으로 쉽게 쓸 수 있게 해주는 SDK를 통해 이미지 분석을 요청할 수 있습니다 

직접 데이터셋을 만들고 모델을 학습하지 않아도 이미지 분석 기능을 빠르게 사용할 수 있습니다.

이를 통해 아이디어를 실제 동작하는 데모로 빠르게 구현할 수 있습니다.

그렇게 세이브 한 시간과 비용을 토대로 구조 설계를 구체화 할 수 있습니다. 

## 2. 개인 식별을 하지 않는 방향으로 설계 가능

이 실시간 예약 관리 시스템은 얼굴 인식이나 개인 식별을 목표로 하지 않습니다. 사람의 이름이나 신원을 확인하는 것이 아니라, 공간 안에 사람이 있는지와 대략적인 점유 상태를 확인하는 것이 목적입니다.

Azure AI Vision에서는 이와 같은 Face부분의 얼굴인식과 개인식별이라는 기능을 Image Analysis 분야의 사람 인식과는 별개로 두고 있기 때문에 설계 구조에서 이를 크게 해결할 수 있습니다. 

[https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/computer-vision/image-analysis-transparency-note](https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/computer-vision/image-analysis-transparency-note)

다만 카메라 기반 시스템인 만큼 개인정보 이슈가 완전히 사라지는 것은 아닙니다. 따라서 Azure AI Vision으로 어떠한 실제 운영을 하시게 된다면 다음과 같은 정책이 필요합니다.

- 원본 이미지 저장 최소화 또는 미저장
- 분석 결과만 저장
- 얼굴 식별 기능 사용 금지
- 촬영 목적과 범위 안내
- 관리자 접근 권한 제한
- 사용자의 동의와 공지 절차 마련

즉, Azure AI Vision을 사용한다고 해서 개인정보 문제가 자동으로 해결되는 것은 아닙니다. 중요한 것은 기술을 어떤 방식으로 설계하고 운영하느냐입니다.

## 3. Azure 서비스와의 확장성

Azure AI Vision은 Azure Functions, 데이터베이스, 웹 서비스, Power BI 등 다른 Azure 서비스와 연결해 확장하기 쉽습니다.

예를 들어 이미지 분석 결과를 데이터베이스에 저장하고, 예약 시스템과 비교한 뒤, 이상 상황이 발생하면 사용자나 관리자에게 알림을 보낼 수 있습니다.

## 데모

## 데모 목적

데모의 목적은 단순히 Azure AI Vision이 사람을 감지할 수 있다는 것을 보여주는 데서 끝나지 않습니다.

데모의 목표는 다음과 같습니다.

> 이미지 분석 결과를 이용해 팀플룸의 상태를 “사용 중”, “비어 있음”, “일시 자리 비움 가능성”으로 판단하는 것입니다.
> 

즉, AI Vision의 결과를 도서관 예약 시스템을 예로 들어 실제 서비스 판단 로직으로 바꾸는 과정을 보여주는 것이 핵심입니다.

## 데모에서 사용한 기능

| **기능** | **활용 방식** |
| --- | --- |
| People Detection | 공간 안의 사람 감지 |
| Object Detection | 노트북, 가방, 책 등 사용 흔적 감지 |
| Confidence Threshold | 신뢰도 낮은 감지 결과 제거 |
| IoU 기반 NMS | 같은 사람의 중복 감지 제거 |
| 상태 판단 로직 | 최종 공간 상태 결정 |

## 기본 데모 코드(ms learn 제공코드. 기본적인 동작 과정을 위함)

```python
# quick_start.py
import os
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

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
    credential=AzureKeyCredential(key)
)

# Get a caption for the image. This will be a synchronously (blocking) call.
result = client.analyze_from_url(
    image_url="https://learn.microsoft.com/azure/ai-services/computer-vision/media/quickstarts/presentation.png",
    visual_features=[VisualFeatures.CAPTION, VisualFeatures.READ],
    gender_neutral_caption=True,  # Optional (default is False)
)

print("Image analysis results:")
# Print caption results to the console
print(" Caption:")
if result.caption is not None:
    print(f"   '{result.caption.text}', Confidence {result.caption.confidence:.4f}")

# Print text (OCR) analysis results to the console
print(" Read:")
if result.read is not None:
    for line in result.read.blocks[0].lines:
        print(f"   Line: '{line.text}', Bounding box {line.bounding_polygon}")
        for word in line.words:
            print(f"     Word: '{word.text}', Bounding polygon {word.bounding_polygon}, Confidence {word.confidence:.4f}")
```

#### 역할

- **Azure Vision 이미지 분석 SDK를 이용해서 웹 이미지 URL을 분석**
- **이미지 설명 Caption과 이미지 속 글자 OCR 결과를 출력**

#### 흐름

1. Azure Vision을 사용하기 위한 SDK 모듈(버전 4.0)을 불러오기
    1. sdk 설치 코드 : `pip install azure-ai-vision-imageanalysis`
    2. `ImageAnalysisClient` : Azure Vision 이미지 분석 요청을 보내는 클라이언트
    3. `VisualFeatures` : 어떤 분석 기능을 사용할지 선택하는 옵션
2. **이미지 분석 클라이언트 생성**
    1. Azure Vision에 요청을 보낼 수 있는 **클라이언트 객체**를 만드는 작업
3. **이미지 URL 분석 요청**
    1. 지정한 이미지 URL을 Azure Vision에 보내고, 두 가지 기능을 수행
        1. `VisualFeatures.CAPTION` : 이미지 전체에 대한 설명 문장 생성
        2. `VisualFeatures.READ` : 이미지 안의 글자를 읽는 **OCR 기능**
    2. 즉,
        1. 이 이미지가 어떤 이미지인지 설명하고
        2. 이미지 안에 적힌 글자를 읽음

→ 여기까지가 OCR(Optical Charactrer Recognition) 광학문자인식 기능 구현

→ 즉, 이미지 속 텍스트를 추출하는 것

## 최종 데모 코드

### 코드

```python
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

```

## 데모 흐름

1. 팀플룸이나 좌석 공간의 이미지를 일정 주기로 수집한다. (파일 하나 받는것으로 구현)
2. Azure AI Vision에 이미지를 전송한다.
3. People Detection으로 사람 수와 위치를 분석한다.
4. Object Detection으로 개인 물건이나 좌석 관련 객체를 분석한다.
5. confidence threshold와 중복 제거 과정을 통해 감지 결과를 정리한다.
6. 정리된 결과를 바탕으로 공간 상태를 판단한다.
7. 예약 시스템의 상태와 비교한다.
8. 불일치 상황이 감지되면 사용자 또는 관리자에게 알림을 보낸다. (세가지 상태로 구분지음)

### 기본 데모 코드에서의 변경점, 코드 설명에서 강조할 부분.

#### 1. **이미지 입력 방식**

```python
with open("teamroom.jpg", "rb") as f:
    image_data = f.read()
client.analyze(image_data=image_data, ...)
```

**URL 이미지 분석 → 로컬 이미지 분석**으로 바뀜

실제 서비스에서는 CCTV 이미지, 주기적으로 촬영된 공간 이미지, 또는 관리 시스템에서 전달받은 이미지가 입력으로 사용될 수 있습니다.

#### **2. 분석 기능 변경**

```python
visual_features=[VisualFeatures.PEOPLE, VisualFeatures.OBJECTS]
```

이번 데모에서는 두 가지 기능을 사용합니다.

- `PEOPLE`: 이미지 안의 사람 감지
- `OBJECTS`: 이미지 안의 사물(객체) 감지

이 두 정보를 함께 사용해 공간 상태를 판단합니다.

#### 3. **사람 수 판단 기능 추가**

`filter_people_detections()` 함수 → 사람 감지 결과를 후처리

단순히 people detection 을 출력하는 게 아니라, **최종적으로 몇 명이 있는지 필터링 하여 계산**

#### **4. Confidence threshold 추가**

Azure Vision 결과에는 신뢰도가 낮은 오탐도 포함될 수 있음

예를 들어 confidence가 0.001, 0.02 같은 값은 실제 사람일 가능성이 낮음

그래서 최종 코드에서는 기준값을 설정

```python
PERSON_CONFIDENCE_THRESHOLD = 0.5
```

#### **5. 중복 사람 탐지 제거 기능 추가**

같은 사람을 여러 bounding box로 중복 감지 가능

```python
PERSON_NMS_IOU_THRESHOLD = 0.5
```

→ 이를 막기 위해 최종 코드에는 **IoU 기반 NMS**가 추가

 `calculate_iou()`

`filter_people_detections()`

#### **~~6. Bounding box 처리 함수 추가~~**

~~Azure SDK에서 bounding box가 dict처럼 보이지만 실제로는 객체 형태로 반환될 수 있음. (버전 호환성 문제로 정규화 함.)~~

~~그래서 최종 코드에는 이를 통일하는 함수가 추가~~

#### **7. 개인 물건 감지 기능 추가**

사람이 감지되지 않아도

노트북, 가방, 책, 의자, 테이블 등이 있으면 실제로는 사용자가 잠깐 자리를 비운 상태일 수 있음

```python
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
```

`filter_relevant_objects()`

`is_personal_object()`

`get_object_name_and_confidence()`

#### **8. 팀플룸 상태 판단 로직 추가**

`decide_room_status()`

- 사람 수 >= 1 → 사용 중
- 사람 수 == 0 + 개인 물건 감지 → 일시 자리 비움 가능성
- 사람 수 == 0 + 개인 물건 없음 → 비어 있음

## 케이스 별 시나리오

### **시나리오 1. 예약했지만 사용하지 않는 경우**

A팀이 오후 2시부터 4시까지 팀플룸을 예약

2시 10분이 지나도 Azure Vision 분석 결과 사람 0명

시스템이 예약자에게 알림 전송

“현재 팀플룸을 사용 중인가요?”

응답이 없으면 자동 취소 또는 관리자 확인

→ 기존 시스템의 장점도 유지

### **시나리오 2. 일찍 끝났지만 퇴실하지 않은 경우**

B팀이 오후 3시부터 5시까지 예약

4시에 실제로 모두 퇴실

Azure Vision 분석 결과 일정 시간 동안 사람 0명

**시스템이 “조기 퇴실로 처리할까요?” 알림 전송**

사용자가 확인하면 남은 시간은 다시 예약 가능 상태로 전환

### **시나리오 3. 퇴실 처리 후 계속 사용하는 경우**

C팀이 앱에서 퇴실 처리

하지만 Azure Vision 분석 결과 여전히 사람 4명 감지

시스템이 관리자에게 상태 불일치 알림

다음 예약자와 충돌하기 전에 조치 가능

# 결론(확장) 및 마무리

→ Azure Vision 객체 탐지

→ 사람 수 / 좌석 점유 여부 분석

→ 예약 시스템 정보와 비교

→ 비정상 상태 감지

→ 관리자 또는 사용자에게 알림

현재 많은 좌석·공간 예약 시스템은 예약 정보에만 의존하기 때문에, 실제 이용 상황과의 불일치로 인해 공간활용의 비효율이 발생하고 있습니다. 

예를 들어서 실제 공간에서는 예약했지만 사용하지 않거나, 일찍 나갔지만 퇴실 처리하지 않거나, 퇴실 후에도 계속 사용하는 문제가 발생합니다.

이 문제의 핵심은 예약 시스템이 현실 공간의 상태를 직접 확인하지 못한다는 점입니다.

Azure AI Vision을 활용하면 이미지에서 사람의 존재 여부와 위치 정보를 추출할 수 있고, 이를 예약 데이터와 비교하여 실제 사용 상태와 시스템 상태의 불일치를 감지할 수 있습니다.

## CTA

이번 발표에서 다룬 문제는 단순히 도서관 팀플룸 예약 시스템의 불편함만은 아닙니다.

핵심은 **기존 시스템이 예약 정보는 알고 있지만, 실제 공간의 상태는 알지 못한다는 점**이었습니다.

예약은 되어 있지만 비어 있는 공간, 퇴실 처리는 되었지만 계속 사용 중인 공간처럼 데이터와 현실이 어긋날 때 사용자 경험과 공간 활용 효율은 떨어질 수밖에 없습니다.

Azure AI Vision은 이 문제를 해결하기 위한 하나의 방법이 될 수 있습니다.

이미지를 통해 사람의 존재 여부와 객체 정보를 분석하고, 그 결과를 예약 데이터와 비교하면 시스템은 단순히 “예약됨/비어 있음”만 판단하는 것이 아니라, **실제 사용 상태를 반영한 판단**을 할 수 있게 됩니다.

하지만 오늘 발표의 핵심은 Azure AI Vision 자체가 아닙니다.

중요한 것은 **현실 세계의 상태를 AI로 데이터화하고, 그 데이터를 기존 시스템의 의사결정에 연결하는 관점**입니다.

그래서 여러분도 발표를 듣고 나서 주변 시스템을 볼 때, **“이 시스템이 놓치고 있는 현실 정보는 무엇일까?”, “그 정보를 AI로 데이터화하면 어떤 문제가 해결될까?”** 라는 질문을 던져보면 좋겠습니다.

작게는 도서관 팀플룸과 좌석 예약 시스템부터, 강의실, 회의실, 아니면 전혀 쌩뚱맞은 곳에서까지 비슷한 문제는 다양한 공간에서 발견될 수 있습니다.

결국 AI 서비스 설계의 출발점은 거창한 모델을 만드는 것이 아니라,

**현실의 불편함을 발견하고, 그것을 데이터로 바꾸어 더 나은 판단으로 연결하는 것**입니다.
