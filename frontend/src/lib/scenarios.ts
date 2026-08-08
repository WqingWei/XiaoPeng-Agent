const SCENARIO_INPUT_PROMPTS: Record<string, string> = {
  fatigue_driving: "长途高速驾驶，系统检测到疲劳信号。可以告诉我您现在的驾驶感受或需要的帮助…",
  parent_child: "车主带孩子出行，需要关注儿童安全与后排舒适。可以告诉我您想调整什么…",
  long_distance_charging: "长途行驶中电量较低，需要评估续航并规划充电。可以告诉我您的目的地或补能需求…",
  commute_arrival: "日常通勤即将到达目的地，需要安排停车和到达准备。可以告诉我您的具体需求…",
  robotaxi_cant_find_car: "Robotaxi 已到达上车点，但乘客暂时找不到车辆。可以描述您看到的位置或周边环境…",
  pickup_abnormal: "Robotaxi 上车点存在施工或禁停等异常，需要寻找安全替代点。可以告诉我现场情况…",
  change_destination: "Robotaxi 行程中需要修改目的地，将评估路线、时间和费用变化。请输入新的目的地…",
  passenger_help: "Robotaxi 行程中乘客需要帮助，将优先评估紧急程度。请描述您当前的情况…",
};

const DEFAULT_INPUT_PROMPT = "告诉我您需要什么出行服务…";

export function getScenarioInputPrompt(scenarioId: string | null): string {
  return (scenarioId && SCENARIO_INPUT_PROMPTS[scenarioId]) || DEFAULT_INPUT_PROMPT;
}

