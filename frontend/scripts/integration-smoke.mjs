import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

import { io } from "socket.io-client";

const apiUrl = process.env.INTEGRATION_API_URL ?? "http://127.0.0.1:8000";
const frontendUrl = process.env.INTEGRATION_FRONTEND_URL ?? "http://127.0.0.1:3000";
const expectedThinkingSteps = [
  "intent_analysis",
  "safety_check",
  "orchestrating",
  "generating",
];

const scenarios = [
  { id: "fatigue_driving", message: "我很困", mode: "owner", safety: "L2" },
  { id: "parent_child", message: "带宝宝出门，帮我准备一下", mode: "owner", safety: "L2" },
  { id: "long_distance_charging", message: "续航不够，找个充电站", mode: "owner", safety: "L1" },
  { id: "commute_arrival", message: "快到公司了，帮我找停车位", mode: "owner", safety: "L1" },
  { id: "robotaxi_cant_find_car", message: "我找不到车", mode: "robotaxi", safety: "L0" },
  { id: "pickup_abnormal", message: "这里施工，帮我换个上车点", mode: "robotaxi", safety: "L2", confirmation: true },
  { id: "change_destination", message: "我想改去广州塔", mode: "robotaxi", safety: "L1", confirmation: true },
  { id: "passenger_help", message: "我身体不舒服，需要求助", mode: "robotaxi", safety: "L4" },
];

async function post(path, payload) {
  const response = await fetch(`${apiUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  assert.equal(response.status, 200, `${path} should return HTTP 200`);
  return response.json();
}

function connectSocket() {
  return new Promise((resolve, reject) => {
    const socket = io(apiUrl, {
      transports: ["websocket", "polling"],
      reconnection: false,
      timeout: 5_000,
    });
    const timer = setTimeout(() => {
      socket.disconnect();
      reject(new Error("Socket.IO connection timed out"));
    }, 8_000);
    socket.once("connect", () => {
      clearTimeout(timer);
      resolve(socket);
    });
    socket.once("connect_error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
  });
}

function sendChat(socket, payload) {
  return new Promise((resolve, reject) => {
    const thinking = [];
    let vehicleUpdate = null;
    const timer = setTimeout(() => {
      cleanup();
      reject(new Error(`Agent response timed out for ${payload.session_id}`));
    }, 30_000);

    function cleanup() {
      clearTimeout(timer);
      socket.off("agent_thinking", onThinking);
      socket.off("vehicle_state_update", onVehicleUpdate);
      socket.off("agent_response", onResponse);
      socket.off("agent_error", onError);
    }
    function onThinking(event) {
      if (event.session_id === payload.session_id) thinking.push(event.step);
    }
    function onVehicleUpdate(event) {
      if (event.session_id === payload.session_id) vehicleUpdate = event;
    }
    function onResponse(response) {
      if (response.session_id !== payload.session_id) return;
      cleanup();
      resolve({ response, thinking, vehicleUpdate });
    }
    function onError(error) {
      if (error.session_id && error.session_id !== payload.session_id) return;
      cleanup();
      reject(new Error(`${error.code}: ${error.message}`));
    }

    socket.on("agent_thinking", onThinking);
    socket.on("vehicle_state_update", onVehicleUpdate);
    socket.on("agent_response", onResponse);
    socket.on("agent_error", onError);
    socket.emit("chat_message", payload);
  });
}

function highestSafetyLevel(alerts) {
  const level = Math.max(0, ...alerts.map((alert) => Number(alert.level.slice(1))));
  return `L${level}`;
}

function validateAgentResponse(result, scenario) {
  const { response, thinking, vehicleUpdate } = result;
  assert.deepEqual(thinking, expectedThinkingSteps, `${scenario.id}: thinking step order`);
  assert.ok(vehicleUpdate?.vehicle, `${scenario.id}: vehicle_state_update missing`);
  assert.equal(vehicleUpdate.vehicle.mode, scenario.mode, `${scenario.id}: pushed vehicle mode`);
  assert.ok(response.user_response, `${scenario.id}: empty user response`);
  assert.ok(Array.isArray(response.service_plan.steps), `${scenario.id}: service plan missing`);
  assert.ok(Array.isArray(response.tool_results), `${scenario.id}: tool results missing`);
  assert.ok(response.reasoning.detected_intent, `${scenario.id}: reasoning missing`);
  assert.ok(response.reasoning.confidence >= 0 && response.reasoning.confidence <= 1, `${scenario.id}: confidence invalid`);
  assert.ok(Array.isArray(response.safety_alerts), `${scenario.id}: safety alerts missing`);
  assert.ok(Array.isArray(response.forbidden_actions), `${scenario.id}: forbidden actions missing`);
  assert.equal(highestSafetyLevel(response.safety_alerts), scenario.safety, `${scenario.id}: safety level`);
  for (const step of response.service_plan.steps) {
    assert.ok(
      response.tool_results.some((resultItem) => resultItem.step_id === step.step_id),
      `${scenario.id}: tool result missing for step ${step.step_id}`,
    );
  }
  if (scenario.confirmation) {
    assert.equal(response.follow_up.needs_confirmation, true, `${scenario.id}: confirmation flag`);
    assert.ok(response.follow_up.suggested_replies.length > 0, `${scenario.id}: suggested replies missing`);
  }
}

async function validateSafetyColorSource() {
  const source = await readFile(
    new URL("../src/components/SafetyAlertCard.tsx", import.meta.url),
    "utf8",
  );
  for (const [level, color] of Object.entries({
    L0: "emerald",
    L1: "yellow",
    L2: "orange",
    L3: "red",
    L4: "animate-pulse",
  })) {
    assert.match(source, new RegExp(`${level}:.*${color}`), `${level} color mapping missing`);
  }
}

async function validateStep14UiSource() {
  const [styles, page, drawer, sceneSelector, statusBar] = await Promise.all([
    readFile(new URL("../src/app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../src/app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../src/components/AgentDrawer.tsx", import.meta.url), "utf8"),
    readFile(new URL("../src/components/SceneSelector.tsx", import.meta.url), "utf8"),
    readFile(new URL("../src/components/StatusBar.tsx", import.meta.url), "utf8"),
  ]);

  assert.match(styles, /--xpeng-green: #00c15d/, "XPeng brand green missing");
  assert.match(styles, /agent-card-in/, "agent card entrance animation missing");
  assert.match(styles, /tool-step-highlight/, "tool step highlight animation missing");
  assert.match(styles, /scene-content\[data-transition="exiting"\]/, "scene exit animation missing");
  assert.match(page, /xl:grid-cols-\[240px_minmax\(0,1fr\)_400px\]/, "1280px desktop layout missing");
  assert.match(drawer, /xl:hidden/, "responsive Agent drawer missing");
  assert.match(drawer, /min-width: 1280px/, "drawer breakpoint guard missing");
  assert.match(sceneSelector, /setSceneTransition\("exiting"\)/, "scene exit state missing");
  assert.match(sceneSelector, /setSceneTransition\("entering"\)/, "scene enter state missing");
  assert.match(statusBar, /AnimatedNumber/, "vehicle number animation missing");
}

const pageResponse = await fetch(frontendUrl);
assert.equal(pageResponse.status, 200, "frontend should return HTTP 200");
await validateSafetyColorSource();
await validateStep14UiSource();

const socket = await connectSocket();
const summaries = [];
try {
  for (const scenario of scenarios) {
    const sessionId = `step14-${scenario.id}`;
    const state = await post("/api/scenario", {
      session_id: sessionId,
      scenario_id: scenario.id,
    });
    assert.equal(state.state.vehicle.mode, scenario.mode, `${scenario.id}: scenario mode`);
    assert.ok(state.state.vehicle.location.address, `${scenario.id}: vehicle location missing`);
    assert.equal(typeof state.state.environment.weather.temperature, "number", `${scenario.id}: weather missing`);

    const result = await sendChat(socket, {
      session_id: sessionId,
      message: scenario.message,
      mode: scenario.mode,
    });
    validateAgentResponse(result, scenario);

    if (scenario.id === "change_destination") {
      const suggestedReply = result.response.follow_up.suggested_replies[0];
      const followUp = await sendChat(socket, {
        session_id: sessionId,
        message: suggestedReply,
        mode: scenario.mode,
      });
      assert.deepEqual(followUp.thinking, expectedThinkingSteps, "suggested reply thinking order");
      assert.equal(followUp.response.turn_id, 2, "suggested reply should create second turn");
    }

    summaries.push({
      scenario: scenario.id,
      turn: result.response.turn_id,
      tools: result.response.service_plan.steps.length,
      safety: highestSafetyLevel(result.response.safety_alerts),
      confirmation: result.response.follow_up.needs_confirmation,
    });
  }
} finally {
  socket.disconnect();
}

console.log(JSON.stringify({ ok: true, scenarios: summaries }, null, 2));
