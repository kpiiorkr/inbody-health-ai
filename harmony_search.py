"""
하모니서치 알고리즘 기반 운동 일정 최적화 모듈
사용자의 목표, 가용 시간, 선호도를 고려한 최적 운동 스케줄 생성
"""
import random
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class HarmonySearch:
    """하모니서치 알고리즘 구현"""
    
    def __init__(self, 
                 harmony_memory_size: int = 10,
                 hmcr: float = 0.9,  # Harmony Memory Considering Rate
                 par: float = 0.3,   # Pitch Adjusting Rate
                 iterations: int = 50):
        self.hms = harmony_memory_size
        self.hmcr = hmcr
        self.par = par
        self.iterations = iterations
        self.harmony_memory = []
    
    def optimize_schedule(self, 
                         available_time: int,
                         exercise_preference: str,
                         analysis: Dict,
                         days: int = 7) -> Dict:
        """
        최적 운동 스케줄 생성
        
        Args:
            available_time: 일일 운동 가능 시간(분)
            exercise_preference: 선호 운동 타입
            analysis: AI 분석 결과
            days: 일정 기간(일)
        
        Returns:
            최적화된 운동 스케줄
        """
        # 초기 하모니 메모리 생성
        self._initialize_harmony_memory(available_time, exercise_preference, days)
        
        # 반복적으로 최적화
        for iteration in range(self.iterations):
            new_harmony = self._improvise_new_harmony(available_time, exercise_preference, days)
            new_fitness = self._calculate_fitness(new_harmony, available_time, analysis)
            
            # 최악의 하모니 찾기
            worst_idx = min(range(len(self.harmony_memory)), 
                          key=lambda i: self.harmony_memory[i]['fitness'])
            
            # 새 하모니가 더 좋으면 교체
            if new_fitness > self.harmony_memory[worst_idx]['fitness']:
                self.harmony_memory[worst_idx] = {
                    'schedule': new_harmony,
                    'fitness': new_fitness
                }
        
        # 최적 하모니 선택
        best_harmony = max(self.harmony_memory, key=lambda h: h['fitness'])
        
        return self._format_schedule(best_harmony['schedule'], available_time, analysis)
    
    def _initialize_harmony_memory(self, available_time: int, preference: str, days: int):
        """초기 하모니 메모리 생성"""
        self.harmony_memory = []
        
        for _ in range(self.hms):
            schedule = self._generate_random_schedule(available_time, preference, days)
            fitness = self._calculate_fitness(schedule, available_time, {})
            self.harmony_memory.append({
                'schedule': schedule,
                'fitness': fitness
            })
    
    def _generate_random_schedule(self, available_time: int, preference: str, days: int) -> List[Dict]:
        """랜덤 운동 스케줄 생성"""
        schedule = []
        
        exercise_types = self._get_exercise_types(preference)
        intensities = ['낮음', '중간', '높음']
        
        for day in range(days):
            if random.random() > 0.3:  # 70% 확률로 운동
                exercise_type = random.choice(exercise_types)
                duration = random.randint(max(20, available_time - 20), available_time)
                intensity = random.choice(intensities)
                
                schedule.append({
                    'day': day + 1,
                    'exercise_type': exercise_type,
                    'duration': duration,
                    'intensity': intensity
                })
            else:
                schedule.append({
                    'day': day + 1,
                    'exercise_type': '휴식',
                    'duration': 0,
                    'intensity': '없음'
                })
        
        return schedule
    
    def _improvise_new_harmony(self, available_time: int, preference: str, days: int) -> List[Dict]:
        """새로운 하모니 즉흥 생성"""
        new_schedule = []
        exercise_types = self._get_exercise_types(preference)
        intensities = ['낮음', '중간', '높음']
        
        for day in range(days):
            if random.random() < self.hmcr:
                # 하모니 메모리에서 선택
                random_harmony = random.choice(self.harmony_memory)
                day_schedule = random_harmony['schedule'][day].copy()
                
                # Pitch Adjustment
                if random.random() < self.par:
                    if day_schedule['exercise_type'] != '휴식':
                        day_schedule['duration'] = min(available_time, 
                                                      max(20, day_schedule['duration'] + random.randint(-15, 15)))
                        day_schedule['intensity'] = random.choice(intensities)
            else:
                # 완전히 새로운 값 생성
                if random.random() > 0.3:
                    day_schedule = {
                        'day': day + 1,
                        'exercise_type': random.choice(exercise_types),
                        'duration': random.randint(max(20, available_time - 20), available_time),
                        'intensity': random.choice(intensities)
                    }
                else:
                    day_schedule = {
                        'day': day + 1,
                        'exercise_type': '휴식',
                        'duration': 0,
                        'intensity': '없음'
                    }
            
            new_schedule.append(day_schedule)
        
        return new_schedule
    
    def _calculate_fitness(self, schedule: List[Dict], available_time: int, analysis: Dict) -> float:
        """스케줄의 적합도 계산"""
        fitness = 0.0
        
        # 1. 운동 빈도 (주 3-5회가 이상적)
        workout_days = sum(1 for d in schedule if d['exercise_type'] != '휴식')
        if 3 <= workout_days <= 5:
            fitness += 30
        elif workout_days == 2 or workout_days == 6:
            fitness += 20
        else:
            fitness += 10
        
        # 2. 시간 활용도
        total_time = sum(d['duration'] for d in schedule)
        target_time = available_time * 4  # 주 4회 기준
        time_ratio = min(total_time / target_time, 1.0) if target_time > 0 else 0
        fitness += time_ratio * 25
        
        # 3. 강도 분포 (낮음, 중간, 높음이 균형있게)
        intensity_count = {'낮음': 0, '중간': 0, '높음': 0}
        for d in schedule:
            if d['intensity'] in intensity_count:
                intensity_count[d['intensity']] += 1
        
        intensity_balance = 1 - (max(intensity_count.values()) - min(intensity_count.values())) / max(1, workout_days)
        fitness += intensity_balance * 20
        
        # 4. 휴식 일정 (연속 2일 이상 운동 방지)
        consecutive_workouts = 0
        max_consecutive = 0
        for d in schedule:
            if d['exercise_type'] != '휴식':
                consecutive_workouts += 1
                max_consecutive = max(max_consecutive, consecutive_workouts)
            else:
                consecutive_workouts = 0
        
        if max_consecutive <= 3:
            fitness += 15
        elif max_consecutive <= 5:
            fitness += 10
        else:
            fitness += 5
        
        # 5. 운동 다양성
        unique_exercises = len(set(d['exercise_type'] for d in schedule if d['exercise_type'] != '휴식'))
        fitness += min(unique_exercises * 5, 10)
        
        return fitness
    
    def _get_exercise_types(self, preference: str) -> List[str]:
        """선호도에 따른 운동 타입 목록"""
        base_exercises = {
            '유산소': ['러닝', '사이클', '수영', '빠르게 걷기', 'HIIT'],
            '근력 운동': ['웨이트 트레이닝', '맨몸 운동', '덤벨 운동', '케틀벨', '밴드 운동'],
            '복합 운동': ['크로스핏', '서킷 트레이닝', '유산소+근력', '기능성 운동'],
            '요가/필라테스': ['요가', '필라테스', '스트레칭', '코어 운동']
        }
        
        return base_exercises.get(preference, base_exercises['복합 운동'])
    
    def _format_schedule(self, schedule: List[Dict], available_time: int, analysis: Dict) -> Dict:
        """스케줄을 출력 형식으로 변환"""
        days_kr = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        
        formatted_plan = []
        total_time = 0
        total_calories = 0
        
        for i, day_plan in enumerate(schedule):
            if day_plan['exercise_type'] != '휴식':
                # 칼로리 계산 (대략적)
                calories = self._estimate_calories(
                    day_plan['exercise_type'], 
                    day_plan['duration'], 
                    day_plan['intensity']
                )
                total_calories += calories
                total_time += day_plan['duration']
                
                goal = self._get_exercise_goal(day_plan['exercise_type'], day_plan['intensity'])
                
                formatted_plan.append({
                    'day': days_kr[i],
                    'exercise': day_plan['exercise_type'],
                    'duration': day_plan['duration'],
                    'intensity': day_plan['intensity'],
                    'goal': goal,
                    'estimated_calories': calories
                })
            else:
                formatted_plan.append({
                    'day': days_kr[i],
                    'exercise': '휴식 또는 가벼운 스트레칭',
                    'duration': 0,
                    'intensity': '없음',
                    'goal': '회복 및 재충전',
                    'estimated_calories': 0
                })
        
        # 목표 달성 예상 기간 계산
        workout_days = sum(1 for d in schedule if d['exercise_type'] != '휴식')
        if workout_days >= 4:
            timeframe = "8-10주"
        elif workout_days >= 3:
            timeframe = "10-12주"
        else:
            timeframe = "12-16주"
        
        return {
            'exercise_plan': formatted_plan,
            'weekly_summary': {
                'total_exercise_time': total_time,
                'estimated_calories': total_calories,
                'workout_days': workout_days,
                'goal_timeframe': timeframe
            }
        }
    
    def _estimate_calories(self, exercise_type: str, duration: int, intensity: str) -> int:
        """칼로리 소모량 추정"""
        # 기본 칼로리/분 (70kg 성인 기준)
        base_calories = {
            '러닝': 10, '사이클': 8, '수영': 9, '빠르게 걷기': 5, 'HIIT': 12,
            '웨이트 트레이닝': 6, '맨몸 운동': 7, '덤벨 운동': 6, '케틀벨': 8, '밴드 운동': 5,
            '크로스핏': 11, '서킷 트레이닝': 10, '유산소+근력': 8, '기능성 운동': 7,
            '요가': 3, '필라테스': 4, '스트레칭': 2, '코어 운동': 5
        }
        
        intensity_multiplier = {'낮음': 0.7, '중간': 1.0, '높음': 1.3}
        
        base = base_calories.get(exercise_type, 7)
        multiplier = intensity_multiplier.get(intensity, 1.0)
        
        return int(base * duration * multiplier)
    
    def _get_exercise_goal(self, exercise_type: str, intensity: str) -> str:
        """운동 타입과 강도에 따른 목표 설정"""
        goals = {
            '러닝': '심폐지구력 향상',
            '사이클': '하체 근력 및 지구력',
            '수영': '전신 근력 및 유연성',
            '빠르게 걷기': '기초 체력 및 체지방 감소',
            'HIIT': '체지방 감소 및 대사량 증가',
            '웨이트 트레이닝': '근력 및 근육량 증가',
            '맨몸 운동': '기능성 근력 향상',
            '덤벨 운동': '상체 근력 강화',
            '케틀벨': '전신 근력 및 폭발력',
            '밴드 운동': '근지구력 및 관절 안정성',
            '크로스핏': '전신 체력 및 폭발력',
            '서킷 트레이닝': '체지방 감소 및 근지구력',
            '유산소+근력': '균형잡힌 체력 발달',
            '기능성 운동': '일상 동작 능력 향상',
            '요가': '유연성 및 정신 건강',
            '필라테스': '코어 강화 및 자세 교정',
            '스트레칭': '유연성 및 회복',
            '코어 운동': '복부 근력 및 안정성'
        }
        
        return goals.get(exercise_type, '전반적인 건강 증진')


def generate_optimal_schedule(
    analysis: Dict,
    available_time: int,
    exercise_preference: str
) -> Dict:
    """
    하모니서치로 최적 운동 일정 생성
    
    Args:
        analysis: AI 분석 결과
        available_time: 일일 운동 가능 시간(분)
        exercise_preference: 선호 운동 타입
    
    Returns:
        최적화된 주간 운동 스케줄
    """
    hs = HarmonySearch(
        harmony_memory_size=10,
        hmcr=0.9,
        par=0.3,
        iterations=50
    )
    
    optimal_schedule = hs.optimize_schedule(
        available_time=available_time,
        exercise_preference=exercise_preference,
        analysis=analysis,
        days=7
    )
    
    return optimal_schedule


if __name__ == "__main__":
    # 테스트 코드
    test_analysis = {
        "overall_assessment": "체중 감량 필요",
        "improvement_goals": ["체중 5kg 감량", "근육량 증가"]
    }
    
    schedule = generate_optimal_schedule(
        analysis=test_analysis,
        available_time=60,
        exercise_preference="복합 운동"
    )
    
    print("✅ 최적 일정 생성 완료:")
    print(f"주간 운동 시간: {schedule['weekly_summary']['total_exercise_time']}분")
    print(f"예상 칼로리 소모: {schedule['weekly_summary']['estimated_calories']} kcal")
    print(f"운동 일수: {schedule['weekly_summary']['workout_days']}일")