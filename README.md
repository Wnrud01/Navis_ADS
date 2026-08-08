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

## 📊 모션 플래닝 평가 방식 (Planning Evaluation Standards)

본 프로젝트는 **DX Challenge 공식 모션 플래닝 평가 및 RideFlux Score 규격**을 준수합니다.

### 1. RideFlux Score (종합 플래닝 점수)
$$\text{RideFlux Score} = \frac{7 \cdot \text{Progress Ratio} + 3 \cdot \text{Comfort}}{10} \times (1 - \text{Overlap}) \times (1 - \text{Offroad})$$

* **Progress Ratio (진행률 - 70% 가중치)**: 목적지까지 전진한 거리에 비례하는 비율 (0.0 ~ 1.0)
* **Comfort Score (승차감 - 30% 가중치)**: 허용 가속도 및 Jerk 기준을 만족하는 승차감 적정 타임스텝 비율 (0.0 ~ 1.0)
* **Overlap Gate (충돌 게이트)**: 주변 차량/보행자와 충돌 시 해당 에피소드 **0점 처리**
* **Offroad Gate (도로 이탈 게이트)**: 도로 경계 이탈 시 해당 에피소드 **0점 처리**

### 2. Error Score (미래 궤적 예측 오차 및 추론 속도)
$$\text{Error Score} = \frac{1}{2} (\text{minADE}_1 + \text{minADE}_6) \times \left(1 + \frac{\max(0, T_{\text{infer}} - 100)}{200}\right)$$

* **minADE₁ / minADE₆**: Top-1 및 Top-6 대표 궤적 오차 (m)
* **T_infer (추론 속도)**: 100ms 초과 시 속도 벌점 배율 부여

---

## 🚀 렌더링 및 평가 실행 방법 (Usage)

### 1. 모션 플래닝 평가 실행
```bash
python evaluate_planning.py
```

### 2. 시나리오 렌더링 구동
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
