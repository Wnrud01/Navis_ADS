# Navis_ADS 🚗💨
> **Waymo Open Motion Dataset (WOMD) 20-Second Scenario Renderer & Autonomous Driving Simulator**

Navis_ADS는 Waymo Open Motion Dataset의 20초 원본 `Scenario Protobuf` TFRecord 시나리오 데이터를 고화질 2D 벡타 차선 지도(Vector Map) 및 멀티 에이전트 애니메이션으로 시각화하고 주행 시뮬레이션을 구동하기 위한 저장소입니다.

---

## 📁 프로젝트 구조 (Repository Structure)

```text
Navis_ADS/
├── data/
│   └── uncompressed_scenario_training_20s_training_20s.tfrecord-00001-of-01000  # 20초 시나리오 데이터
├── render_waymo_scenario.py  # 20초 시나리오 전용 렌더링 스크립트
├── requirements.txt          # 파이썬 의존성 패키지 목록
└── README.md                 # 프로젝트 및 설치/실행 가이드 문서
```

---

## 🛠️ 설치 가이드 (Installation Guide)

Ubuntu (WSL 포함) 및 Linux 파이썬 환경에서 가상환경(`venv`)을 세팅하는 3단계 과정입니다.

### 1단계: 가상환경 생성 (Virtual Environment)
```bash
python3 -m venv ~/.venvs/navis_ads
```

### 2단계: 가상환경 활성화 (Activation)
```bash
source ~/.venvs/navis_ads/bin/activate
```

*(Tip: 접속할 때마다 자동으로 가상환경이 켜지게 하려면: `echo "source ~/.venvs/navis_ads/bin/activate" >> ~/.bashrc`)*

### 3단계: 필수 라이브러리 설치 (Install Dependencies)
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚀 렌더링 실행 방법 (Usage)

가상환경이 활성화된 상태에서 아래 명령어로 시나리오 렌더링을 실행할 수 있습니다:

### 기본 렌더링 구동
```bash
python render_waymo_scenario.py
```

### 커스텀 옵션으로 구동
```bash
python render_waymo_scenario.py \
  --tfrecord_path "data/uncompressed_scenario_training_20s_training_20s.tfrecord-00001-of-01000" \
  --output_gif "outputs/my_scenario_rendering.gif" \
  --fps 10
```

---

## 🎨 시각화 구성 요소 (Visual Features)

* **SDC (자율주행 차량 - 하늘색)**: 자율주행 차량 지오메트리 다각형 및 1초 주행 이력 궤적
* **Vehicle (일반 주변 차량 - 주황색)**: 차선 위 동적 주변 차량 다각형
* **Pedestrian (보행자 - 빨간색)**: 보행자 다각형
* **Cyclist (자전거 - 초록색)**: 자전거 다각형
* **Vector Map (도로 지도 - 회색)**: `lane` (차선), `road_line` (도로 표시선), `road_edge` (도로 경계), `crosswalk` (횡단보도), `stop_sign` (정지 표지판)
