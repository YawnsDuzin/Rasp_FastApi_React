=======================================
2025.12.27(토)
=======================================

아래의 명령은 라즈베리파이에서만 실행되는 스크립트 코드인지 확인해서 알려줘.

# 설치 스크립트 실행 (라즈베리파이 자동 감지)
chmod +x scripts/install.sh
./scripts/install.sh

[추가프롬프트]
윈도우pc에서는 안되는거지?

[추가2]
README.md 파일에 리눅스/라즈베리파이, 윈도우PC 둘다 나눠서 설치 및 실행 가능하도록 추가작성해줘.

=======================================

(venv) D:\dzp\바이브코딩\Rasp_FastApi_React\backend>pip install -r requirements.txt
Collecting fastapi==0.109.0 (from -r requirements.txt (line 2))
  Using cached fastapi-0.109.0-py3-none-any.whl.metadata (24 kB)
Collecting uvicorn==0.27.0 (from uvicorn[standard]==0.27.0->-r requirements.txt (line 3))
  Using cached uvicorn-0.27.0-py3-none-any.whl.metadata (6.4 kB)
Collecting python-multipart==0.0.6 (from -r requirements.txt (line 4))
  Using cached python_multipart-0.0.6-py3-none-any.whl.metadata (2.5 kB)
Collecting websockets==12.0 (from -r requirements.txt (line 5))
  Using cached websockets-12.0-py3-none-any.whl.metadata (6.6 kB)
Collecting sqlalchemy==2.0.25 (from -r requirements.txt (line 8))
  Using cached SQLAlchemy-2.0.25-py3-none-any.whl.metadata (9.6 kB)
Collecting aiosqlite==0.19.0 (from -r requirements.txt (line 9))
  Using cached aiosqlite-0.19.0-py3-none-any.whl.metadata (4.3 kB)
Collecting psutil==5.9.8 (from -r requirements.txt (line 12))
  Using cached psutil-5.9.8-cp37-abi3-win_amd64.whl.metadata (22 kB)
Collecting numpy==1.26.3 (from -r requirements.txt (line 27))
  Using cached numpy-1.26.3.tar.gz (15.7 MB)
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
  Installing backend dependencies ... done
  Preparing metadata (pyproject.toml) ... error
  error: subprocess-exited-with-error
  
  × Preparing metadata (pyproject.toml) did not run successfully.
  │ exit code: 2
  ╰─> [35 lines of output]
      + D:\dzp\바이브코딩\Rasp_FastApi_React\backend\venv\Scripts\python.exe C:\Users\dzP\AppData\Local\Temp\pip-install-5tg_gj63\numpy_d6c03a52f72f45acb4e7cee6232c2d88\vendored-meson\meson\meson.py setup C:\Users\dzP\AppData\Local\Temp\pip-install-5tg_gj63\numpy_d6c03a52f72f45acb4e7cee6232c2d88 C:\Users\dzP\AppData\Local\Temp\pip-install-5tg_gj63\numpy_d6c03a52f72f45acb4e7cee6232c2d88\.mesonpy-shsz4hn4\build -Dbuildtype=release -Db_ndebug=if-release -Db_vscrt=md --native-file=C:\Users\dzP\AppData\Local\Temp\pip-install-5tg_gj63\numpy_d6c03a52f72f45acb4e7cee6232c2d88\.mesonpy-shsz4hn4\build\meson-python-native-file.ini
      Traceback (most recent call last):
        File "C:\Users\dzP\AppData\Local\Temp\pip-install-5tg_gj63\numpy_d6c03a52f72f45acb4e7cee6232c2d88\vendored-meson\meson\mesonbuild\mesonmain.py", line 194, in run
          return options.run_func(options)
                 ~~~~~~~~~~~~~~~~^^^^^^^^^
        File "C:\Users\dzP\AppData\Local\Temp\pip-install-5tg_gj63\numpy_d6c03a52f72f45acb4e7cee6232c2d88\vendored-meson\meson\mesonbuild\msetup.py", line 358, in run
          app.generate()
          ~~~~~~~~~~~~^^
        File "C:\Users\dzP\AppData\Local\Temp\pip-install-5tg_gj63\numpy_d6c03a52f72f45acb4e7cee6232c2d88\vendored-meson\meson\mesonbuild\msetup.py", line 178, in generate
          env = environment.Environment(self.source_dir, self.build_dir, self.options)
        File "C:\Users\dzP\AppData\Local\Temp\pip-install-5tg_gj63\numpy_d6c03a52f72f45acb4e7cee6232c2d88\vendored-meson\meson\mesonbuild\environment.py", line 571, in __init__
          config = coredata.parse_machine_files(self.coredata.config_files)
        File "C:\Users\dzP\AppData\Local\Temp\pip-install-5tg_gj63\numpy_d6c03a52f72f45acb4e7cee6232c2d88\vendored-meson\meson\mesonbuild\coredata.py", line 1032, in parse_machine_files
          parser = MachineFileParser(filenames)
        File "C:\Users\dzP\AppData\Local\Temp\pip-install-5tg_gj63\numpy_d6c03a52f72f45acb4e7cee6232c2d88\vendored-meson\meson\mesonbuild\coredata.py", line 973, in __init__
          self.parser.read(filenames)
          ~~~~~~~~~~~~~~~~^^^^^^^^^^^
        File "C:\Users\dzP\AppData\Local\Temp\pip-install-5tg_gj63\numpy_d6c03a52f72f45acb4e7cee6232c2d88\vendored-meson\meson\mesonbuild\coredata.py", line 960, in read
          return super().read(filenames, encoding)
                 ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
        File "C:\Users\dzP\AppData\Local\Programs\Python\Python313\Lib\configparser.py", line 737, in read
          self._read(fp, filename)
          ~~~~~~~~~~^^^^^^^^^^^^^^
        File "C:\Users\dzP\AppData\Local\Programs\Python\Python313\Lib\configparser.py", line 1052, in _read
          ParsingError._raise_all(self._read_inner(fp, fpname))
                                  ~~~~~~~~~~~~~~~~^^^^^^^^^^^^
        File "C:\Users\dzP\AppData\Local\Programs\Python\Python313\Lib\configparser.py", line 1060, in _read_inner
          for st.lineno, line in enumerate(map(Line, fp), start=1):
                                 ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
        File "<frozen codecs>", line 325, in decode
      UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb9 in position 31: invalid start byte
     
      ERROR: Unhandled python exception
     
          This is a Meson bug and should be reported!
      [end of output]

  note: This error originates from a subprocess, and is likely not a problem with pip.
error: metadata-generation-failed

× Encountered error while generating package metadata.
╰─> numpy

note: This is an issue with the package mentioned above, not pip.
hint: See above for details.

=======================================

(venv) D:\dzp\바이브코딩\Rasp_FastApi_React\backend>pip install -r requirements.txt
Collecting fastapi==0.109.0 (from -r requirements.txt (line 2))
  Using cached fastapi-0.109.0-py3-none-any.whl.metadata (24 kB)
Collecting uvicorn==0.27.0 (from uvicorn[standard]==0.27.0->-r requirements.txt (line 3))
  Using cached uvicorn-0.27.0-py3-none-any.whl.metadata (6.4 kB)
Collecting python-multipart==0.0.6 (from -r requirements.txt (line 4))
  Using cached python_multipart-0.0.6-py3-none-any.whl.metadata (2.5 kB)
Collecting websockets==12.0 (from -r requirements.txt (line 5))
  Using cached websockets-12.0-py3-none-any.whl.metadata (6.6 kB)
Collecting sqlalchemy==2.0.25 (from -r requirements.txt (line 8))
  Using cached SQLAlchemy-2.0.25-py3-none-any.whl.metadata (9.6 kB)
Collecting aiosqlite==0.19.0 (from -r requirements.txt (line 9))
  Using cached aiosqlite-0.19.0-py3-none-any.whl.metadata (4.3 kB)
Collecting psutil==5.9.8 (from -r requirements.txt (line 12))
  Using cached psutil-5.9.8-cp37-abi3-win_amd64.whl.metadata (22 kB)
Collecting numpy>=1.26.0 (from -r requirements.txt (line 27))
  Downloading numpy-2.4.0-cp313-cp313-win_amd64.whl.metadata (6.6 kB)
Collecting pydantic==2.5.3 (from -r requirements.txt (line 28))
  Using cached pydantic-2.5.3-py3-none-any.whl.metadata (65 kB)
Collecting pydantic-settings==2.1.0 (from -r requirements.txt (line 29))
  Using cached pydantic_settings-2.1.0-py3-none-any.whl.metadata (2.9 kB)
Collecting aiofiles==23.2.1 (from -r requirements.txt (line 32))
  Downloading aiofiles-23.2.1-py3-none-any.whl.metadata (9.7 kB)
Collecting python-json-logger==2.0.7 (from -r requirements.txt (line 35))
  Downloading python_json_logger-2.0.7-py3-none-any.whl.metadata (6.5 kB)
Collecting starlette==0.35.1 (from -r requirements.txt (line 38))
  Using cached starlette-0.35.1-py3-none-any.whl.metadata (5.8 kB)
Collecting pytest==7.4.4 (from -r requirements.txt (line 41))
  Using cached pytest-7.4.4-py3-none-any.whl.metadata (7.9 kB)
Collecting pytest-asyncio==0.23.3 (from -r requirements.txt (line 42))
  Using cached pytest_asyncio-0.23.3-py3-none-any.whl.metadata (3.9 kB)
Collecting httpx==0.26.0 (from -r requirements.txt (line 43))
  Using cached httpx-0.26.0-py3-none-any.whl.metadata (7.6 kB)
Collecting python-dotenv==1.0.0 (from -r requirements.txt (line 46))
  Using cached python_dotenv-1.0.0-py3-none-any.whl.metadata (21 kB)
Collecting typing-extensions>=4.8.0 (from fastapi==0.109.0->-r requirements.txt (line 2))
  Using cached typing_extensions-4.15.0-py3-none-any.whl.metadata (3.3 kB)
Collecting annotated-types>=0.4.0 (from pydantic==2.5.3->-r requirements.txt (line 28))
  Using cached annotated_types-0.7.0-py3-none-any.whl.metadata (15 kB)
Collecting pydantic-core==2.14.6 (from pydantic==2.5.3->-r requirements.txt (line 28))
  Using cached pydantic_core-2.14.6.tar.gz (360 kB)
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
  Installing backend dependencies ... done
  Preparing metadata (pyproject.toml) ... error
  error: subprocess-exited-with-error

  × Preparing metadata (pyproject.toml) did not run successfully.
  │ exit code: 1
  ╰─> [23 lines of output]
      Python reports SOABI: cp313-win_amd64
      Computed rustc target triple: x86_64-pc-windows-msvc
      Installation directory: C:\Users\dzP\AppData\Local\puccinialin\puccinialin\Cache
      Rustup already downloaded
      Installing rust to C:\Users\dzP\AppData\Local\puccinialin\puccinialin\Cache\rustup
      warn: It looks like you have an existing rustup settings file at:
      warn: C:\Users\dzP\.rustup\settings.toml
      warn: Rustup will install the default toolchain as specified in the settings file,
      warn: instead of the one inferred from the default host triple.
      info: profile set to 'minimal'
      info: default host triple is x86_64-pc-windows-msvc
      warn: Updating existing toolchain, profile choice will be ignored
      info: syncing channel updates for 'stable-x86_64-pc-windows-msvc'
      info: default toolchain set to 'stable-x86_64-pc-windows-msvc'
      Checking if cargo is installed
      cargo 1.92.0 (344c4567c 2025-10-21)
     
      Cargo, the Rust package manager, is not installed or is not on PATH.
      This package requires Rust and Cargo to compile extensions. Install it through
      the system's package manager or via https://rustup.rs/
     
      Checking for Rust toolchain....
      Rust not found, installing into a temporary directory
      [end of output]

  note: This error originates from a subprocess, and is likely not a problem with pip.
error: metadata-generation-failed

× Encountered error while generating package metadata.
╰─> pydantic-core

note: This is an issue with the package mentioned above, not pip.
hint: See above for details.

=======================================

윈도우pc에서 시물레이션 으로 테스트 중인데, 첨부이미지와 같이 화면에 아무것도 표시안되는 것 같아.
확인해줘.

=======================================

"hardware" 화면에  "버튼"도 있어야 되는거 아니야?? 그리고 다른 누락된것이 더 있는지 
수정하지말고, 확인하고 정리해서 알려줘.

[요약]
    누락 항목	위치	      설명
    버튼 상태	Hardware,    Dashboard	4개 버튼 상태 표시 (읽기 전용)
    OLED 제어  Hardware	    텍스트 쓰기 기능
    LCD 제어   Hardware	    텍스트 쓰기/지우기 기능
수정이 필요하시면 말씀해주세요!

[추가프롬프트]
누락된 사항 추가해줘.

=======================================

햄버거 메뉴 (class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700") 를 
class="h-16 flex items-center justify-center border-b border-gray-200 dark:border-gray-700" 의 우측에 표시하는게 더 자연스럽고 일반적인 방법이 아닌지 알려줘.

[추가1]
gmail은 첨부이미지와 같이 상단좌측에 있는것 같은데,,
[추가2]
Gmail 스타일로 변경하려면 햄버거 메뉴를 사이드바 로고 영역 좌측으로 옮기는 방법으로 수정해줘.
[추가3]
접으니깐 첨부이미지와 같이 로고가 겹쳐서 표시되고 있어. 이거 어떻게 처리하는게 일바적인지 알려줘
    [제안]
    Gmail에서는 사이드바가 접히면:
        햄버거 메뉴만 남음
        로고는 숨겨짐
[추가4]
"추천: Gmail 스타일 (방법 1)" 으로 수정작업 진행해줘.'

=======================================

첨부이미지의 Settings 의 Simulation Controls 가 표시/제어가 둘다 안되는것 같은데,
확인해줘.

=======================================

현재 수정된 부분 관련된 모든 문서 최신으로 업데이트해줘.

[완료] 문서 업데이트 완료:

## 변경 사항 요약

### 1. Backend (sensor_controller.py)
- 시뮬레이션 모드에서 수동 설정된 센서 값의 자동 드리프트 비활성화
- `_manually_set` 딕셔너리 추가로 수동 설정 값 추적
- 온도, 습도, 거리, 모션, 조도, 토양수분 모두 지원

### 2. Backend (requirements.txt)
- 고정 버전(`==`)에서 유연한 버전(`>=`)으로 변경
- Windows/Linux 호환성 개선
- starlette 별도 의존성 제거 (fastapi에 포함됨)

### 3. Frontend (Layout.tsx)
- Gmail 스타일 사이드바 레이아웃 적용
- 햄버거 메뉴를 사이드바 상단 좌측으로 이동
- 사이드바 접힘 시 로고 숨김 처리

### 4. Frontend (Dashboard.tsx)
- 버튼 상태 표시 섹션 추가 (읽기 전용)
- 3열 그리드 레이아웃으로 변경 (LED, Button, Relay)
- CircleDot 아이콘으로 버튼 상태 시각화

### 5. Frontend (Hardware.tsx)
- 버튼 상태 모니터링 카드 추가 (읽기 전용)
- LCD 디스플레이 제어 추가 (텍스트 쓰기, 행 선택, 화면 지우기)
- OLED 디스플레이 정보 카드 추가
- Monitor, Type, CircleDot 아이콘 추가

### 6. Frontend (vite.config.ts)
- WebSocket 프록시 설정 추가 (`ws: true`)

=======================================

/init
/clear

=======================================

현재 frontend 에서 shadcn/ui  를 사용하고 있는지 확인해서 알려줘.

[추가1]
shadcn/ui 를 사용하는게 트렌드에 더 맞지 않아?? 
[추가2]
[opus]
shadcn/ui 로 변경해줘. 기존의 커스텀 컴포넌트들도 모두 마이그레이션 해줘.

=======================================

(venv) D:\dzp\바이브코딩\Rasp_FastApi_React\backend>uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
INFO:     Will watch for changes in these directories: ['D:\\dzp\\바이브코딩\\Rasp_FastApi_React\\backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [69552] using WatchFiles
Process SpawnProcess-1:
Traceback (most recent call last):
  File "C:\Users\dzP\AppData\Local\Programs\Python\Python313\Lib\multiprocessing\process.py", line 313, in _bootstrap
    self.run()
    ~~~~~~~~^^
  File "C:\Users\dzP\AppData\Local\Programs\Python\Python313\Lib\multiprocessing\process.py", line 108, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\dzp\바이브코딩\Rasp_FastApi_React\backend\venv\Lib\site-packages\uvicorn\_subprocess.py", line 80, in subprocess_started
    target(sockets=sockets)
    ~~~~~~^^^^^^^^^^^^^^^^^
  File "D:\dzp\바이브코딩\Rasp_FastApi_React\backend\venv\Lib\site-packages\uvicorn\server.py", line 67, in run
    return asyncio_run(self.serve(sockets=sockets), loop_factory=self.config.get_loop_factory())
  File "C:\Users\dzP\AppData\Local\Programs\Python\Python313\Lib\asyncio\runners.py", line 195, in run
    return runner.run(main)
           ~~~~~~~~~~^^^^^^
  File "C:\Users\dzP\AppData\Local\Programs\Python\Python313\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Users\dzP\AppData\Local\Programs\Python\Python313\Lib\asyncio\base_events.py", line 725, in run_until_complete
    return future.result()
           ~~~~~~~~~~~~~^^
  File "D:\dzp\바이브코딩\Rasp_FastApi_React\backend\venv\Lib\site-packages\uvicorn\server.py", line 71, in serve
    await self._serve(sockets)
  File "D:\dzp\바이브코딩\Rasp_FastApi_React\backend\venv\Lib\site-packages\uvicorn\server.py", line 78, in _serve
    config.load()
    ~~~~~~~~~~~^^
  File "D:\dzp\바이브코딩\Rasp_FastApi_React\backend\venv\Lib\site-packages\uvicorn\config.py", line 439, in load
    self.loaded_app = import_from_string(self.app)
                      ~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "D:\dzp\바이브코딩\Rasp_FastApi_React\backend\venv\Lib\site-packages\uvicorn\importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
  File "C:\Users\dzP\AppData\Local\Programs\Python\Python313\Lib\importlib\__init__.py", line 88, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1331, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 1026, in exec_module
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "D:\dzp\바이브코딩\Rasp_FastApi_React\backend\app\main.py", line 27, in <module>
    from app.core.config import settings
  File "D:\dzp\바이브코딩\Rasp_FastApi_React\backend\app\core\__init__.py", line 2, in <module>
    from .config import settings
  File "D:\dzp\바이브코딩\Rasp_FastApi_React\backend\app\core\config.py", line 131, in <module>
    settings = Settings()
  File "D:\dzp\바이브코딩\Rasp_FastApi_React\backend\venv\Lib\site-packages\pydantic_settings\main.py", line 194, in __init__
    super().__init__(
    ~~~~~~~~~~~~~~~~^
        **__pydantic_self__._settings_build_values(
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<27 lines>...
        )
        ^
    )
    ^
  File "D:\dzp\바이브코딩\Rasp_FastApi_React\backend\venv\Lib\site-packages\pydantic\main.py", line 250, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
pydantic_core._pydantic_core.ValidationError: 9 validation errors for Settings
I2C_LCD_ADDRESS
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='0x27', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/int_parsing
I2C_OLED_ADDRESS
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='0x3C', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/int_parsing
I2C_BMP280_ADDRESS
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='0x76', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/int_parsing
I2C_ADS1115_ADDRESS
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='0x48', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/int_parsing
LED_PINS
  Extra inputs are not permitted [type=extra_forbidden, input_value='17,27,22,23', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
BUTTON_PINS
  Extra inputs are not permitted [type=extra_forbidden, input_value='5,6,13,19', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
RELAY_PINS
  Extra inputs are not permitted [type=extra_forbidden, input_value='24,25', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
PWM_MOTOR_PIN
  Extra inputs are not permitted [type=extra_forbidden, input_value='18', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
PWM_SERVO_PIN
  Extra inputs are not permitted [type=extra_forbidden, input_value='12', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden

=======================================

[opus]
전체코드(FrontEnd, BackEnd 포함) 에 코드 줄 별로 최대한 자세한 주석을 작성해줘.
FAST API, React 등 사용된 언어 및 라이브러리가 모두 익숙하지 않아.
최대한 자세하게 주석을 작성해줘. 현재의 코드를 전체적으로 분석해서, 새로운 기능을 추가하고, 원하는 부분을 수정을 하고 싶어서 최대한 자세하게 코드를 분석하고 싶어서 그래
--context7 --sequential-thinking

[작업결과]
모든 주석에서 다음 내용을 상세히 설명했습니다:
React 개념: useState, useEffect, 조건부 렌더링
TypeScript: 인터페이스, 타입, 제네릭
Tailwind CSS: 반응형 디자인, 다크 모드
shadcn/ui: Card, Button, Switch, Slider 등
Recharts: LineChart, AreaChart, Tooltip
Zustand: 전역 상태 관리
WebSocket: 실시간 통신
SVG: 게이지 차트 원리 (strokeDasharray/strokeDashoffset)


[추가프롬프트]
주석 누락된 소스코드가 있는지 다시 한번 확인해줘.

[추가1]
주석보완이 필요한 파일들 주석 다 추가해줘.

=======================================

docs에 있는 파일들을 중복된 파일은 정리해서 제거해주고,
FontEnd, BackEnd 가 구조적으로 어떻게 연동되는지 최대한 자세하게 설명하는
문서도 추가해줘.
--context7 --sequential-thinking

[추가1]
docs 폴더의 api, architecture, deployment, hardware 폴더는 하나의 폴더로 통합하는게 관리하기 더 좋지 않을까?

=======================================

/init


[변경_사항]
1.단일 테스트 실행 명령어 추가
  Backend: pytest tests/test_hardware.py -v, pytest tests/test_api.py::test_led -v
  Frontend: npm run test -- --run src/hooks/useStore.test.ts
2.프로덕션 빌드 & 배포 섹션 추가
  React 빌드 후 backend/static 폴더로 복사하는 과정 명시
3.Hardware Controllers 설명 수정
  Thread pool executor → asyncio.to_thread() (실제 코드와 일치)
4.Data Flow 섹션 추가
  REST API vs WebSocket 역할을 한눈에 파악 가능
5.Documentation 섹션 추가
  docs/ 폴더의 플랫 구조와 각 문서 역할 안내


/clear

=======================================

변경된 부분 git push 처리해줘.

=======================================
=======================================
=======================================
=======================================
=======================================
=======================================
=======================================

시물레이션 모드에서 데이터 표시 는 어떻게 처리되는지 확인하고, 정리해서 알려줘.

=======================================
=======================================
=======================================
=======================================
=======================================