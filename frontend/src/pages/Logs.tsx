/**
 * Logs Page (로그 페이지)
 * ========================
 *
 * [한국어 설명]
 * 시스템 로그와 이벤트 기록을 조회하고 관리하는 페이지입니다.
 * 로그 레벨 필터링, 시간 범위 선택, 오래된 로그 정리 기능을 제공합니다.
 *
 * [주요 기능]
 * 1. 로그 조회: 백엔드 DB에서 로그 데이터 가져오기
 * 2. 레벨 필터: DEBUG, INFO, WARNING, ERROR, CRITICAL 필터링
 * 3. 시간 필터: 1시간~7일 범위 선택
 * 4. 자동 갱신: 30초마다 새 로그 가져오기
 * 5. 로그 정리: 오래된 로그 삭제 (데이터 유지 기간 기준)
 *
 * [로그 레벨 설명]
 * - DEBUG: 개발/디버깅용 상세 정보
 * - INFO: 일반 정보 메시지
 * - WARNING: 주의가 필요한 상황
 * - ERROR: 오류 발생
 * - CRITICAL: 심각한 오류 (시스템 중단 가능)
 *
 * [컴포넌트 구조]
 * Logs
 *  ├── Filter Bar (필터 컨트롤)
 *  │    ├── Level Filter (레벨 선택 버튼들)
 *  │    ├── Time Range (기간 드롭다운)
 *  │    └── Actions (새로고침, 정리 버튼)
 *  ├── Log Count (표시된 로그 수)
 *  └── Log List (로그 항목들)
 */

// ==================== Imports ====================

// [React Hooks]
import { useState, useEffect } from 'react';

// [API 서비스]
// dataApi: 로그 데이터 관련 REST API
import { dataApi } from '../services/api';

// [shadcn/ui 컴포넌트]
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

// [Select 컴포넌트]
// 시간 범위 선택용 드롭다운
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

// [cn 유틸리티]
// 조건부 클래스명 병합
import { cn } from '@/lib/utils';

// [Lucide 아이콘]
import {
  FileText,       // 기본 로그 아이콘
  AlertCircle,    // 에러/크리티컬
  AlertTriangle,  // 경고
  Info,           // 정보
  Bug,            // 디버그
  RefreshCw,      // 새로고침
  Trash2,         // 삭제/정리
} from 'lucide-react';


// ==================== 타입 정의 ====================

/**
 * [LogEntry 인터페이스]
 * 로그 항목의 데이터 구조 정의
 *
 * [필드 설명]
 * - id: 로그 고유 식별자 (DB 기본키)
 * - timestamp: 로그 생성 시간 (ISO 8601 형식)
 * - level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
 * - source: 로그 출처 (예: 'GPIO Controller', 'WebSocket')
 * - message: 로그 메시지 본문
 * - details: 추가 정보 객체 (선택적)
 * - user_action: 사용자 액션 여부 (true면 사용자가 발생시킨 이벤트)
 */
interface LogEntry {
  id: number;
  timestamp: string;
  level: string;
  source: string;
  message: string;
  details: Record<string, unknown> | null;  // 동적 객체 또는 null
  user_action: boolean;
}

/**
 * [LOG_LEVELS 상수]
 * 필터링에 사용되는 로그 레벨 목록
 * 'ALL'은 모든 레벨 표시
 */
const LOG_LEVELS = ['ALL', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];


// ==================== Logs 컴포넌트 ====================
/**
 * [Logs 함수형 컴포넌트]
 * 로그 페이지의 메인 컴포넌트
 */
export default function Logs() {
  // ==================== 상태 관리 ====================

  // [로그 데이터 상태]
  // 백엔드에서 가져온 로그 배열
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // [로딩 상태]
  // API 호출 중 표시용
  const [loading, setLoading] = useState(true);

  // [선택된 로그 레벨]
  // 'ALL' 또는 특정 레벨
  const [selectedLevel, setSelectedLevel] = useState('ALL');

  // [시간 범위 (시간 단위)]
  // '1', '6', '24', '72', '168' (문자열)
  const [hours, setHours] = useState('24');

  // ==================== 로그 가져오기 함수 ====================
  /**
   * [fetchLogs 함수]
   * 백엔드 API에서 로그 데이터 가져오기
   *
   * [파라미터 처리]
   * - level: 'ALL'이면 undefined로 전달 (필터 없음)
   * - hours: 문자열을 정수로 변환
   * - limit: 최대 200개 로그
   */
  const fetchLogs = async () => {
    setLoading(true);
    try {
      // 'ALL'이면 undefined (서버에서 모든 레벨 반환)
      const level = selectedLevel === 'ALL' ? undefined : selectedLevel;

      // API 호출
      const data = await dataApi.getSystemLogs(level, parseInt(hours), 200);

      // [Type Assertion]
      // API 반환 타입을 LogEntry 배열로 변환
      // 'as unknown as'는 타입 불일치 시 이중 변환 패턴
      setLogs(data as unknown as LogEntry[]);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    }
    setLoading(false);
  };

  // ==================== 자동 갱신 ====================
  /**
   * [useEffect로 자동 갱신 설정]
   * 컴포넌트 마운트 시 및 필터 변경 시 로그 가져오기
   * 30초마다 자동 갱신
   */
  useEffect(() => {
    // 초기 데이터 로드
    fetchLogs();

    // [setInterval로 주기적 갱신]
    // 30000ms = 30초
    const interval = setInterval(fetchLogs, 30000);

    // [클린업 함수]
    // 컴포넌트 언마운트 시 인터벌 정리
    // 메모리 누수 방지
    return () => clearInterval(interval);
  }, [selectedLevel, hours]);
  // [의존성 배열]
  // selectedLevel 또는 hours 변경 시 effect 재실행

  // ==================== 헬퍼 함수들 ====================

  /**
   * [getLevelIcon 함수]
   * 로그 레벨에 따른 아이콘 반환
   *
   * @param level - 로그 레벨 문자열
   * @returns JSX.Element - Lucide 아이콘 컴포넌트
   */
  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'CRITICAL':
      case 'ERROR':
        // 빨간 원 안에 느낌표 아이콘
        return <AlertCircle className="w-4 h-4" />;
      case 'WARNING':
        // 노란 삼각형 경고 아이콘
        return <AlertTriangle className="w-4 h-4" />;
      case 'INFO':
        // 정보 아이콘 (i)
        return <Info className="w-4 h-4" />;
      case 'DEBUG':
        // 벌레 아이콘 (디버깅)
        return <Bug className="w-4 h-4" />;
      default:
        // 기본 파일 아이콘
        return <FileText className="w-4 h-4" />;
    }
  };

  /**
   * [getLevelVariant 함수]
   * 로그 레벨에 따른 Badge 스타일 반환
   *
   * [Badge Variants]
   * - destructive: 빨간색 (에러)
   * - warning: 노란색 (경고)
   * - default: 기본색 (정보)
   * - secondary: 회색 (디버그)
   *
   * @param level - 로그 레벨 문자열
   * @returns Badge variant 문자열
   */
  const getLevelVariant = (level: string): "default" | "destructive" | "secondary" | "outline" | "success" | "warning" => {
    switch (level) {
      case 'CRITICAL':
      case 'ERROR':
        return 'destructive';  // 빨간색
      case 'WARNING':
        return 'warning';      // 노란색
      case 'INFO':
        return 'default';      // 기본색
      case 'DEBUG':
        return 'secondary';    // 회색
      default:
        return 'secondary';
    }
  };

  // ==================== 이벤트 핸들러 ====================

  /**
   * [handleCleanup 함수]
   * 오래된 로그 데이터 정리
   *
   * [확인 다이얼로그]
   * confirm()으로 사용자 확인 후 실행
   * 실수로 삭제 방지
   */
  const handleCleanup = async () => {
    // [confirm 함수]
    // 브라우저 기본 확인 다이얼로그
    // true: 확인, false: 취소
    if (confirm('Are you sure you want to delete old logs?')) {
      try {
        // 30일보다 오래된 데이터 삭제
        const result = await dataApi.cleanupData(30);

        // [alert 함수]
        // 삭제 결과 표시
        alert(`Deleted ${result.deleted_records} old records`);

        // 로그 목록 새로고침
        fetchLogs();
      } catch (error) {
        console.error('Failed to cleanup:', error);
      }
    }
  };

  // ==================== JSX 반환 ====================
  return (
    <div className="space-y-6">

      {/* ==================== 필터 영역 ==================== */}
      <Card>
        <CardContent className="pt-6">
          {/*
            [플렉스 레이아웃 + 래핑]
            flex-wrap: 화면이 좁으면 다음 줄로 넘김
            gap-4: 요소 간 1rem(16px) 간격
          */}
          <div className="flex flex-wrap items-center gap-4">

            {/* ========== 레벨 필터 ========== */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Level:</span>
              <div className="flex gap-1">
                {/*
                  [레벨 버튼 렌더링]
                  LOG_LEVELS 배열을 버튼으로 변환
                */}
                {LOG_LEVELS.map((level) => (
                  <Button
                    key={level}
                    // 선택된 레벨은 기본 스타일, 아니면 보조 스타일
                    variant={selectedLevel === level ? 'default' : 'secondary'}
                    size="sm"
                    onClick={() => setSelectedLevel(level)}
                  >
                    {level}
                  </Button>
                ))}
              </div>
            </div>

            {/* ========== 시간 범위 필터 ========== */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Period:</span>
              {/*
                [Select 컴포넌트]
                드롭다운으로 시간 범위 선택
              */}
              <Select value={hours} onValueChange={setHours}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Select period" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Last 1 hour</SelectItem>
                  <SelectItem value="6">Last 6 hours</SelectItem>
                  <SelectItem value="24">Last 24 hours</SelectItem>
                  <SelectItem value="72">Last 3 days</SelectItem>
                  <SelectItem value="168">Last 7 days</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* ========== 액션 버튼 ========== */}
            {/*
              [ml-auto]
              margin-left: auto로 오른쪽 정렬
            */}
            <div className="flex gap-2 ml-auto">
              {/* 새로고침 버튼 */}
              <Button
                variant="secondary"
                onClick={fetchLogs}
                disabled={loading}
              >
                {/*
                  [조건부 애니메이션]
                  로딩 중이면 회전 애니메이션
                */}
                <RefreshCw className={cn('w-4 h-4 mr-2', loading && 'animate-spin')} />
                Refresh
              </Button>

              {/* 정리 버튼 */}
              <Button
                variant="destructive"  // 빨간색 (위험한 액션)
                onClick={handleCleanup}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Cleanup
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ==================== 로그 개수 표시 ==================== */}
      <div className="text-sm text-muted-foreground">
        Showing {logs.length} log entries
      </div>

      {/* ==================== 로그 목록 ==================== */}
      {/*
        [overflow-hidden]
        카드 모서리가 둥글어도 내용이 넘치지 않도록
      */}
      <Card className="overflow-hidden">
        {/*
          [p-0]
          CardContent의 기본 패딩 제거
          로그 항목이 카드 가장자리까지 채우도록
        */}
        <CardContent className="p-0">

          {/* 로딩 상태 */}
          {loading && logs.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              {/* 회전하는 로딩 아이콘 */}
              <RefreshCw className="w-8 h-8 animate-spin text-primary" />
            </div>

          /* 빈 상태 */
          ) : logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              {/* 연한 파일 아이콘 */}
              <FileText className="w-12 h-12 text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground">No logs found</p>
            </div>

          /* 로그 목록 */
          ) : (
            /*
              [divide-y]
              자식 요소들 사이에 수평선 추가
              Tailwind의 divide 유틸리티
            */
            <div className="divide-y">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="p-4 hover:bg-muted/50 transition-colors"
                >
                  {/*
                    [로그 항목 레이아웃]
                    왼쪽: 레벨 배지
                    오른쪽: 내용 (출처, 시간, 메시지)
                  */}
                  <div className="flex items-start gap-4">

                    {/* 레벨 배지 */}
                    {/*
                      [Badge 컴포넌트]
                      작은 태그/라벨 형태의 UI
                      variant: 색상 스타일
                    */}
                    <Badge variant={getLevelVariant(log.level)} className="flex items-center gap-1">
                      {getLevelIcon(log.level)}
                      {log.level}
                    </Badge>

                    {/* 로그 내용 */}
                    {/*
                      [min-w-0]
                      플렉스 아이템이 줄어들 수 있도록 허용
                      긴 텍스트가 넘치는 것 방지
                    */}
                    <div className="flex-1 min-w-0">
                      {/* 첫 줄: 출처, 시간, 사용자 액션 배지 */}
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium">
                          {log.source}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {/*
                            [Date 포맷팅]
                            ISO 문자열을 로컬 날짜/시간으로 변환
                          */}
                          {new Date(log.timestamp).toLocaleString()}
                        </span>
                        {/* 사용자 액션 배지 (조건부) */}
                        {log.user_action && (
                          <Badge variant="success" className="text-xs">
                            User Action
                          </Badge>
                        )}
                      </div>

                      {/* 메시지 본문 */}
                      {/*
                        [break-words]
                        긴 단어가 있으면 줄바꿈
                      */}
                      <p className="text-sm text-muted-foreground break-words">
                        {log.message}
                      </p>

                      {/* 상세 정보 (있는 경우) */}
                      {log.details && (
                        /*
                          [pre 태그]
                          코드/JSON 표시용 (고정폭 폰트)
                          JSON.stringify: 객체를 문자열로 변환
                          null, 2: 들여쓰기 2칸으로 포맷팅
                        */
                        <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-x-auto">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
