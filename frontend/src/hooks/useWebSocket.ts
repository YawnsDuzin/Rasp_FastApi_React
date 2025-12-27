/**
 * WebSocket Hook (WebSocket 연결 훅)
 * ====================================
 *
 * [한국어 설명]
 * WebSocket 연결을 관리하는 React 커스텀 훅입니다.
 * 컴포넌트에서 이 훅을 호출하면 자동으로 WebSocket 연결이 설정됩니다.
 *
 * [WebSocket이란?]
 * - HTTP와 달리 양방향 실시간 통신 프로토콜
 * - 서버가 클라이언트에게 먼저 데이터를 보낼 수 있음 (Push)
 * - 연결 유지 비용이 낮아 실시간 데이터에 적합
 *
 * [커스텀 훅 패턴]
 * - 'use'로 시작하는 함수
 * - React 훅들을 조합하여 재사용 가능한 로직 생성
 * - 여러 컴포넌트에서 동일한 로직 공유
 *
 * [이 훅의 역할]
 * 1. WebSocket 연결 설정 및 관리
 * 2. 메시지 수신 및 전역 상태 업데이트
 * 3. 자동 재연결 처리
 * 4. 시스템 경고 알림 생성
 */

// ==================== Imports ====================

// [React Hooks]
// useEffect: 부수효과 처리 (연결 설정, 정리)
// useCallback: 함수 메모이제이션 (불필요한 재생성 방지)
import { useEffect, useCallback } from 'react';

// [WebSocket 서비스]
// 실제 WebSocket 연결을 관리하는 싱글톤 서비스
// 이 훅은 서비스를 사용하고, 상태를 Zustand에 연결하는 역할
import { websocketService } from '../services/websocket';

// [Zustand 스토어]
// 전역 상태 관리
import { useStore } from './useStore';

// [타입 정의]
// TypeScript 인터페이스들
import { HardwareData, SystemMetrics, WebSocketMessage } from '../types';


// ==================== useWebSocket 훅 ====================
/**
 * [useWebSocket 함수]
 * WebSocket 연결을 관리하는 커스텀 훅
 *
 * [사용 방법]
 * // 기본 사용 - 연결만 필요한 경우
 * useWebSocket();
 *
 * // 반환값 사용 - 수동 제어가 필요한 경우
 * const { isConnected, send, subscribe } = useWebSocket();
 *
 * [동작 흐름]
 * 1. 컴포넌트 마운트 시 WebSocket 연결
 * 2. 메시지 수신 시 handleMessage 호출
 * 3. 메시지 타입에 따라 전역 상태 업데이트
 * 4. 컴포넌트 언마운트 시 핸들러 정리
 */
export function useWebSocket() {
  // ==================== Zustand 상태 및 액션 추출 ====================
  /**
   * [객체 구조 분해 할당]
   * useStore()에서 필요한 상태 업데이트 함수들만 추출
   *
   * - setConnected: 연결 상태 업데이트
   * - setHardwareData: 하드웨어 데이터 업데이트
   * - setSystemMetrics: 시스템 메트릭 업데이트
   * - addAlert: 경고 알림 추가
   */
  const { setConnected, setHardwareData, setSystemMetrics, addAlert } = useStore();

  // ==================== 메시지 핸들러 ====================
  /**
   * [useCallback Hook]
   * 함수를 메모이제이션(캐싱)하여 불필요한 재생성 방지
   *
   * [왜 useCallback을 사용하는가?]
   * - handleMessage가 매 렌더링마다 새로 생성되면
   * - useEffect의 의존성 배열이 변경되어 effect가 재실행됨
   * - 이로 인해 이벤트 핸들러가 반복적으로 등록/해제됨
   *
   * [useCallback 구조]
   * useCallback(
   *   () => { ... },  // 메모이제이션할 함수
   *   [dep1, dep2]    // 의존성 배열 - 이 값들이 변경될 때만 함수 재생성
   * )
   */
  const handleMessage = useCallback(
    // [메시지 처리 함수]
    // WebSocketMessage 타입의 메시지를 받아 처리
    (message: WebSocketMessage) => {
      // [switch문으로 메시지 타입별 처리]
      // message.type: 메시지 종류를 나타내는 문자열
      switch (message.type) {

        // ==================== 연결 완료 메시지 ====================
        case 'connected':
          // 서버에서 연결 확인 메시지
          // client_id: 서버가 부여한 클라이언트 식별자
          console.log('WebSocket authenticated:', message.client_id);
          break;

        // ==================== 하드웨어 업데이트 ====================
        case 'hardware_update':
          // [하드웨어 데이터 수신]
          // 서버에서 주기적으로 전송하는 GPIO, PWM, 센서 상태
          if (message.data) {
            // [타입 캐스팅]
            // message.data as HardwareData: unknown 타입을 HardwareData로 변환
            // 서버에서 올바른 형식으로 보낸다고 가정
            setHardwareData(message.data as HardwareData);
          }
          break;

        // ==================== 시스템 메트릭 업데이트 ====================
        case 'system_update':
          // [시스템 메트릭 수신]
          // CPU, 메모리, 디스크 사용량 등
          if (message.data) {
            const metrics = message.data as SystemMetrics;
            setSystemMetrics(metrics);

            // ==================== 경고 조건 체크 ====================
            // [CPU 온도 경고]
            // 70°C 초과 시 경고 알림 생성
            // ?. (옵셔널 체이닝): temperature가 undefined일 수 있음
            if (metrics.cpu.temperature && metrics.cpu.temperature > 70) {
              // [템플릿 리터럴]
              // `문자열 ${변수}`: 문자열 내에 변수 삽입
              // toFixed(1): 소수점 1자리까지 표시
              addAlert('warning', `High CPU temperature: ${metrics.cpu.temperature.toFixed(1)}°C`);
            }

            // [메모리 사용량 경고]
            // 90% 초과 시 경고
            if (metrics.memory.percent > 90) {
              addAlert('warning', `High memory usage: ${metrics.memory.percent.toFixed(1)}%`);
            }
          }
          break;

        // ==================== 로그 업데이트 ====================
        case 'log_update':
          // 시스템 로그 업데이트
          // 현재는 처리하지 않음 (필요시 구현)
          // Handle log updates if needed
          break;

        // ==================== 구독 확인 ====================
        case 'subscribed':
          // 토픽 구독 완료 확인 메시지
          // topics: 구독 중인 토픽 목록
          console.log('Subscribed to topics:', message.topics);
          break;

        // ==================== Heartbeat 응답 ====================
        case 'pong':
          // [ping/pong 패턴]
          // 클라이언트가 ping을 보내면 서버가 pong으로 응답
          // 연결 상태 확인에 사용
          // Heartbeat response
          break;

        // ==================== 알 수 없는 메시지 ====================
        default:
          // 정의되지 않은 메시지 타입
          // 디버깅을 위해 콘솔에 출력
          console.log('Unknown message type:', message.type);
      }
    },
    // [의존성 배열]
    // 이 함수들이 변경될 때만 handleMessage 재생성
    // Zustand의 액션 함수들은 안정적(stable)이므로 실제로는 거의 재생성 안 됨
    [setHardwareData, setSystemMetrics, addAlert]
  );

  // ==================== WebSocket 연결 설정 ====================
  /**
   * [useEffect Hook]
   * 컴포넌트 생명주기에 따른 부수효과 처리
   *
   * [실행 시점]
   * 1. 컴포넌트 마운트 시 (처음 렌더링 후)
   * 2. 의존성 배열의 값이 변경될 때
   *
   * [정리(cleanup) 함수]
   * return () => { ... }
   * - 컴포넌트 언마운트 시 실행
   * - 의존성 변경으로 재실행되기 전에 실행
   * - 메모리 누수 방지
   */
  useEffect(() => {
    // ==================== 이벤트 핸들러 등록 ====================

    // [메시지 핸들러 등록]
    // onMessage: 메시지 수신 시 handleMessage 호출
    // 반환값: 구독 해제 함수 (cleanup에서 사용)
    const unsubMessage = websocketService.onMessage(handleMessage);

    // [연결 핸들러 등록]
    // onConnect: 연결 성공 시 setConnected(true) 호출
    // 화살표 함수로 간단하게 작성
    const unsubConnect = websocketService.onConnect(() => setConnected(true));

    // [연결 해제 핸들러 등록]
    // onDisconnect: 연결 끊김 시 setConnected(false) 호출
    const unsubDisconnect = websocketService.onDisconnect(() => setConnected(false));

    // ==================== WebSocket 연결 시작 ====================
    // connect(): WebSocket 연결 시도
    // 이미 연결되어 있으면 아무것도 하지 않음
    websocketService.connect();

    // ==================== Cleanup 함수 ====================
    /**
     * [정리(cleanup) 함수]
     * 컴포넌트 언마운트 시 또는 의존성 변경 전 실행
     *
     * [왜 필요한가?]
     * - 이벤트 핸들러 누수 방지
     * - 같은 핸들러가 중복 등록되는 것 방지
     * - 메모리 누수 방지
     */
    return () => {
      // 모든 핸들러 구독 해제
      unsubMessage();    // 메시지 핸들러 해제
      unsubConnect();    // 연결 핸들러 해제
      unsubDisconnect(); // 연결 해제 핸들러 해제
    };
  }, [handleMessage, setConnected]);
  // [의존성 배열]
  // handleMessage, setConnected가 변경되면 effect 재실행
  // 재실행 시 이전 핸들러 정리 후 새 핸들러 등록

  // ==================== 반환값 ====================
  /**
   * [훅의 반환값]
   * 컴포넌트에서 WebSocket을 직접 제어하고 싶을 때 사용
   *
   * [반환 객체]
   * - isConnected: 현재 연결 상태 (getter)
   * - send: 메시지 전송 함수
   * - subscribe: 토픽 구독 함수
   * - unsubscribe: 토픽 구독 해제 함수
   *
   * [bind 메서드]
   * .bind(websocketService): 함수 내부의 this를 websocketService로 고정
   * 클래스 메서드를 객체에서 분리해서 사용할 때 필요
   *
   * [사용 예시]
   * const { send } = useWebSocket();
   * send({ type: 'custom_message', data: { ... } });
   */
  return {
    // getter로 현재 연결 상태 반환
    isConnected: websocketService.isConnected,

    // 메시지 전송 함수
    // bind로 this 컨텍스트 유지
    send: websocketService.send.bind(websocketService),

    // 토픽 구독 함수
    subscribe: websocketService.subscribe.bind(websocketService),

    // 토픽 구독 해제 함수
    unsubscribe: websocketService.unsubscribe.bind(websocketService),
  };
}
