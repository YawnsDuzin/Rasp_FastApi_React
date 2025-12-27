/**
 * WebSocket Service (WebSocket 서비스)
 * =====================================
 *
 * [한국어 설명]
 * 실시간 데이터 통신을 위한 WebSocket 연결을 관리합니다.
 * 싱글톤 패턴으로 구현되어 앱 전체에서 하나의 연결을 공유합니다.
 *
 * [WebSocket vs HTTP]
 * - HTTP: 요청-응답 모델, 클라이언트가 먼저 요청해야 함
 * - WebSocket: 양방향 통신, 서버가 먼저 데이터를 보낼 수 있음 (Push)
 *
 * [이 서비스의 기능]
 * 1. WebSocket 연결 생성 및 관리
 * 2. 자동 재연결 (지수 백오프)
 * 3. ping/pong 핸들링
 * 4. 메시지/연결/연결해제 이벤트 핸들링
 * 5. 토픽 기반 구독/구독해제
 *
 * [싱글톤 패턴]
 * 클래스의 인스턴스가 하나만 존재하도록 보장
 * 파일 끝에서 인스턴스를 생성하고 export
 */

// ==================== Imports ====================

// [타입 정의]
// WebSocket 메시지의 타입 정의
import { WebSocketMessage } from '../types';


// ==================== 타입 정의 ====================
/**
 * [타입 별칭 (Type Alias)]
 * 함수 타입을 간단하게 정의
 *
 * [MessageHandler]
 * WebSocket 메시지를 처리하는 함수의 타입
 * 매개변수: WebSocketMessage, 반환값: void
 *
 * [ConnectionHandler]
 * 연결/연결해제 이벤트를 처리하는 함수의 타입
 * 매개변수: 없음, 반환값: void
 */
type MessageHandler = (message: WebSocketMessage) => void;
type ConnectionHandler = () => void;


// ==================== WebSocketService 클래스 ====================
/**
 * [WebSocketService 클래스]
 * WebSocket 연결을 관리하는 서비스 클래스
 *
 * [클래스 구조]
 * - private 속성: 외부에서 직접 접근 불가
 * - public 메서드: 외부에서 호출 가능
 * - getter: 속성처럼 접근하지만 계산된 값 반환
 */
class WebSocketService {

  // ==================== Private 속성 ====================

  /**
   * [ws: WebSocket | null]
   * 현재 WebSocket 연결 인스턴스
   * null이면 연결되지 않은 상태
   *
   * [private 키워드]
   * 클래스 외부에서 접근 불가
   * 캡슐화(Encapsulation)를 위해 사용
   */
  private ws: WebSocket | null = null;

  /**
   * [url: string]
   * WebSocket 서버 URL
   * 예: "ws://localhost:8000/api/ws/live"
   */
  private url: string;

  /**
   * [reconnectAttempts: number]
   * 현재까지의 재연결 시도 횟수
   * 성공적으로 연결되면 0으로 리셋
   */
  private reconnectAttempts = 0;

  /**
   * [maxReconnectAttempts: number]
   * 최대 재연결 시도 횟수
   * 이 횟수를 초과하면 재연결 중단
   */
  private maxReconnectAttempts = 5;

  /**
   * [reconnectDelay: number]
   * 기본 재연결 대기 시간 (밀리초)
   * 지수 백오프로 증가함
   */
  private reconnectDelay = 1000;

  /**
   * [messageHandlers: Set<MessageHandler>]
   * 메시지 수신 시 호출될 핸들러 함수들의 집합
   *
   * [Set vs Array]
   * - Set: 중복 허용 안 함, 삽입/삭제 O(1)
   * - Array: 중복 허용, 삭제 시 O(n)
   */
  private messageHandlers: Set<MessageHandler> = new Set();

  /**
   * [connectHandlers: Set<ConnectionHandler>]
   * 연결 성공 시 호출될 핸들러 함수들
   */
  private connectHandlers: Set<ConnectionHandler> = new Set();

  /**
   * [disconnectHandlers: Set<ConnectionHandler>]
   * 연결 해제 시 호출될 핸들러 함수들
   */
  private disconnectHandlers: Set<ConnectionHandler> = new Set();

  /**
   * [isConnecting: boolean]
   * 현재 연결 시도 중인지 여부
   * 중복 연결 시도 방지
   */
  private isConnecting = false;


  // ==================== 생성자 ====================
  /**
   * [constructor]
   * 클래스 인스턴스 생성 시 호출
   *
   * [WebSocket URL 구성]
   * - window.location.protocol: 현재 페이지 프로토콜 (http: 또는 https:)
   * - https: → wss: (보안 WebSocket)
   * - http: → ws: (일반 WebSocket)
   * - window.location.host: 호스트명과 포트 (예: localhost:3000)
   *
   * [프록시 고려]
   * 개발 환경에서 Vite 프록시가 /api 요청을 백엔드로 전달
   * 프로덕션에서는 nginx 등이 프록시 역할
   */
  constructor() {
    // [삼항 연산자로 프로토콜 결정]
    // https: → wss: (보안), http: → ws: (일반)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

    // [WebSocket URL 조합]
    // 템플릿 리터럴로 URL 구성
    this.url = `${protocol}//${window.location.host}/api/ws/live`;
  }


  // ==================== Public 메서드: 연결 관리 ====================

  /**
   * [connect]
   * WebSocket 연결 시작
   *
   * [중복 연결 방지]
   * - 이미 연결되어 있으면 무시
   * - 연결 시도 중이면 무시
   */
  connect(): void {
    // [연결 상태 확인]
    // readyState === WebSocket.OPEN: 이미 연결됨
    // ?.는 옵셔널 체이닝: ws가 null이면 undefined 반환
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;  // 이미 연결되었거나 연결 중이면 종료
    }

    // [연결 시도 플래그 설정]
    this.isConnecting = true;
    console.log('Connecting to WebSocket:', this.url);

    try {
      // ==================== WebSocket 생성 ====================
      /**
       * [new WebSocket(url)]
       * 브라우저 내장 WebSocket 객체 생성
       * 생성 즉시 연결 시도 시작
       */
      this.ws = new WebSocket(this.url);

      // ==================== onopen 이벤트 ====================
      /**
       * [onopen]
       * 연결 성공 시 호출되는 콜백
       *
       * [화살표 함수]
       * this 바인딩이 자동으로 현재 클래스 인스턴스를 가리킴
       */
      this.ws.onopen = () => {
        console.log('WebSocket connected');

        // [상태 초기화]
        this.isConnecting = false;    // 연결 시도 완료
        this.reconnectAttempts = 0;   // 재연결 카운터 리셋

        // [연결 핸들러 호출]
        // Set.forEach(): 모든 핸들러 순회 및 호출
        this.connectHandlers.forEach(handler => handler());

        // [토픽 구독]
        // 연결 후 'all' 토픽 구독 (모든 업데이트 수신)
        this.send({ type: 'subscribe', topics: ['all'] });
      };

      // ==================== onmessage 이벤트 ====================
      /**
       * [onmessage]
       * 서버로부터 메시지 수신 시 호출
       *
       * @param event - MessageEvent 객체
       * @param event.data - 수신된 데이터 (문자열)
       */
      this.ws.onmessage = (event) => {
        try {
          // [JSON 파싱]
          // 서버가 보낸 JSON 문자열을 객체로 변환
          const message: WebSocketMessage = JSON.parse(event.data);

          // [메시지 처리]
          this.handleMessage(message);

        } catch (error) {
          // [파싱 에러]
          // 서버가 잘못된 JSON을 보낸 경우
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      // ==================== onclose 이벤트 ====================
      /**
       * [onclose]
       * 연결 종료 시 호출
       *
       * @param event - CloseEvent 객체
       * @param event.code - 종료 코드 (1000: 정상, 1006: 비정상 등)
       * @param event.reason - 종료 사유 (문자열)
       *
       * [종료 코드]
       * - 1000: 정상 종료
       * - 1001: 페이지 이동
       * - 1006: 비정상 종료 (네트워크 끊김 등)
       */
      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);

        // [상태 업데이트]
        this.isConnecting = false;

        // [연결 해제 핸들러 호출]
        this.disconnectHandlers.forEach(handler => handler());

        // ==================== 자동 재연결 ====================
        /**
         * [지수 백오프 재연결]
         * 재연결 시도 간격을 점점 늘림
         * 서버 과부하 방지
         *
         * [계산식]
         * delay = baseDelay * 2^(attempts-1)
         * 1초 → 2초 → 4초 → 8초 → 16초
         */
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;

          // [지수 백오프 딜레이 계산]
          // Math.pow(2, n-1): 2의 거듭제곱
          // 1초 * 2^0 = 1초, 1초 * 2^1 = 2초, ...
          const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

          console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

          // [setTimeout으로 재연결 예약]
          // 화살표 함수로 this 바인딩 유지
          setTimeout(() => this.connect(), delay);
        }
      };

      // ==================== onerror 이벤트 ====================
      /**
       * [onerror]
       * WebSocket 에러 발생 시 호출
       *
       * [주의]
       * onerror 후에는 보통 onclose도 호출됨
       * 재연결 로직은 onclose에서 처리
       */
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
      };

    } catch (error) {
      // [생성 단계 에러]
      // WebSocket 객체 생성 자체가 실패한 경우
      console.error('Failed to create WebSocket:', error);
      this.isConnecting = false;
    }
  }

  /**
   * [disconnect]
   * WebSocket 연결 종료
   *
   * [수동 종료]
   * 사용자가 명시적으로 연결을 끊을 때 호출
   * 이 경우 재연결 시도 안 함 (onclose에서 reconnectAttempts로 제어)
   */
  disconnect(): void {
    if (this.ws) {
      // [close 호출]
      // 정상 종료 코드(1000)로 연결 종료
      this.ws.close();

      // [참조 해제]
      // 메모리 해제를 위해 null로 설정
      this.ws = null;
    }
  }

  /**
   * [send]
   * WebSocket으로 메시지 전송
   *
   * @param data - 전송할 데이터 (객체)
   *
   * [Record<string, unknown>]
   * 키가 문자열인 객체 타입
   * 어떤 형태의 객체든 전송 가능
   */
  send(data: Record<string, unknown>): void {
    // [연결 상태 확인]
    // readyState === OPEN일 때만 전송 가능
    if (this.ws?.readyState === WebSocket.OPEN) {
      // [JSON 문자열로 변환 후 전송]
      this.ws.send(JSON.stringify(data));
    }
    // 연결되지 않은 상태면 무시 (에러 발생 안 함)
  }


  // ==================== Private 메서드: 내부 처리 ====================

  /**
   * [handleMessage]
   * 수신된 메시지 내부 처리
   *
   * @param message - 파싱된 WebSocket 메시지
   *
   * [ping/pong 핸들링]
   * 서버가 ping을 보내면 즉시 pong 응답
   * 연결 상태 확인용 (heartbeat)
   */
  private handleMessage(message: WebSocketMessage): void {
    // [ping/pong 처리]
    // 서버의 heartbeat에 자동 응답
    if (message.type === 'ping') {
      this.send({ type: 'pong' });
      return;  // ping은 핸들러에 전달하지 않음
    }

    // [등록된 핸들러들에게 메시지 전달]
    // Set의 각 핸들러 함수 호출
    this.messageHandlers.forEach(handler => handler(message));
  }


  // ==================== Public 메서드: 이벤트 구독 ====================

  /**
   * [onMessage]
   * 메시지 수신 핸들러 등록
   *
   * @param handler - 메시지 처리 함수
   * @returns 구독 해제 함수
   *
   * [구독/구독해제 패턴]
   * 함수 등록 시 해제 함수를 반환
   * cleanup 시 반환된 함수 호출로 간편하게 해제
   *
   * [사용 예시]
   * const unsubscribe = ws.onMessage((msg) => console.log(msg));
   * // 나중에...
   * unsubscribe();  // 구독 해제
   */
  onMessage(handler: MessageHandler): () => void {
    // [핸들러 등록]
    this.messageHandlers.add(handler);

    // [구독 해제 함수 반환]
    // 클로저로 handler 참조 유지
    return () => this.messageHandlers.delete(handler);
  }

  /**
   * [onConnect]
   * 연결 성공 핸들러 등록
   *
   * @param handler - 연결 시 호출될 함수
   * @returns 구독 해제 함수
   */
  onConnect(handler: ConnectionHandler): () => void {
    this.connectHandlers.add(handler);
    return () => this.connectHandlers.delete(handler);
  }

  /**
   * [onDisconnect]
   * 연결 해제 핸들러 등록
   *
   * @param handler - 연결 해제 시 호출될 함수
   * @returns 구독 해제 함수
   */
  onDisconnect(handler: ConnectionHandler): () => void {
    this.disconnectHandlers.add(handler);
    return () => this.disconnectHandlers.delete(handler);
  }


  // ==================== Getter ====================

  /**
   * [isConnected getter]
   * 현재 연결 상태 반환
   *
   * [getter 문법]
   * get propertyName() { return value; }
   * 함수지만 속성처럼 접근: ws.isConnected (괄호 없음)
   *
   * [계산된 속성]
   * 호출될 때마다 현재 상태를 계산하여 반환
   */
  get isConnected(): boolean {
    // readyState가 OPEN(1)이면 true
    return this.ws?.readyState === WebSocket.OPEN;
  }


  // ==================== Public 메서드: 토픽 구독 ====================

  /**
   * [subscribe]
   * 토픽 구독
   *
   * @param topics - 구독할 토픽 배열 (예: ['hardware', 'system'])
   *
   * [토픽 종류]
   * - 'hardware': 하드웨어 상태 업데이트
   * - 'system': 시스템 메트릭 업데이트
   * - 'logs': 시스템 로그 업데이트
   * - 'all': 모든 업데이트
   */
  subscribe(topics: string[]): void {
    this.send({ type: 'subscribe', topics });
  }

  /**
   * [unsubscribe]
   * 토픽 구독 해제
   *
   * @param topics - 구독 해제할 토픽 배열
   */
  unsubscribe(topics: string[]): void {
    this.send({ type: 'unsubscribe', topics });
  }
}


// ==================== 싱글톤 인스턴스 ====================
/**
 * [싱글톤 패턴 구현]
 * 모듈 레벨에서 인스턴스를 생성하고 export
 *
 * [왜 싱글톤인가?]
 * - WebSocket 연결은 하나만 필요
 * - 여러 컴포넌트가 같은 연결 공유
 * - 리소스 절약 및 일관성 유지
 *
 * [사용 방법]
 * import { websocketService } from './services/websocket';
 * websocketService.connect();
 */
export const websocketService = new WebSocketService();
