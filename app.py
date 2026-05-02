import streamlit as st

from graph.workflow import build_blockage_workflow, build_route_workflow
from utils.observability import read_observability_records
from utils.observability_report import build_run_summary
from utils.persistence import clear_app_state, load_app_state, save_app_state


st.set_page_config(page_title="AI Workflow Coach", layout="wide")

st.title("AI工作流程教练")
st.caption("先生成完整路线，再进入卡点细化。")


def render_route_result(route_result):
    st.subheader("任务理解")
    st.write(route_result.task_summary)

    st.subheader("路线类型")
    st.write(route_result.route_type)

    st.subheader("完整路线")
    for idx, step in enumerate(route_result.steps, start=1):
        with st.expander(f"Step {idx}｜{step.step_name}", expanded=(idx == 1)):
            st.write(f"**步骤目标：** {step.step_goal}")
            st.write(f"**首选工具：** {step.primary_tool}")
            st.write(f"**备选工具：** {step.backup_tool}")
            st.write(f"**建议输入：** {step.suggested_input}")
            st.write(f"**预期产出：** {step.expected_output}")
            st.write(f"**执行提醒：** {step.execution_tip}")
            st.write(f"**通过标准：** {step.ready_check}")


def render_blockage_result(blockage_result):
    st.subheader("为什么会卡住")
    st.write(blockage_result.why_stuck)

    st.subheader("拆解子步骤")
    for idx, substep in enumerate(blockage_result.substeps, start=1):
        st.write(f"{idx}. {substep}")

    st.subheader("更简单输入")
    st.write(blockage_result.simple_input)

    st.subheader("替代工具")
    st.write(blockage_result.alternative_tool)

    st.subheader("完成标准")
    st.write(blockage_result.done_check)


def render_observability_panel():
    workflow_run_id = st.session_state.get("workflow_run_id", "")
    with st.expander("技术细节 / 运行追踪", expanded=False):
        if not workflow_run_id:
            st.write("暂无运行追踪记录。")
            return

        st.write(f"**workflow_run_id：** `{workflow_run_id}`")
        try:
            summary = build_run_summary(workflow_run_id)
            st.write("**运行摘要**")
            st.json(summary)
        except Exception:
            st.warning("运行摘要生成失败，请查看日志。")

        records = read_observability_records(workflow_run_id)
        if not any(records.values()):
            st.write("暂无运行追踪记录。")
            return

        st.write("**workflow_trace（工作流追踪）**")
        if records["workflow_trace"]:
            st.dataframe(records["workflow_trace"], use_container_width=True)
        else:
            st.write("暂无 workflow_trace。")

        st.write("**model_call_log（模型调用日志）**")
        if records["model_call_log"]:
            st.dataframe(records["model_call_log"], use_container_width=True)
        else:
            st.write("暂无 model_call_log。")

        st.write("**retrieval_trace（检索追踪）**")
        if records["retrieval_trace"]:
            st.dataframe(records["retrieval_trace"], use_container_width=True)
        else:
            st.write("暂无 retrieval_trace。")


def clear_direction_choice_state():
    st.session_state.need_direction_choice = False
    st.session_state.direction_options = []
    st.session_state.selected_direction_option = ""
    st.session_state.custom_direction_option = ""


if "app_state_initialized" not in st.session_state:
    saved_state = load_app_state()
    st.session_state.user_goal = saved_state["user_goal"]
    st.session_state.route_result = saved_state["route_result"]
    st.session_state.blockage_result = saved_state["blockage_result"]
    st.session_state.followup_question = ""
    st.session_state.followup_answer = ""
    st.session_state.last_followup_answer = ""
    st.session_state.effective_goal = ""
    st.session_state.is_waiting_followup = False
    st.session_state.need_direction_choice = False
    st.session_state.direction_options = []
    st.session_state.selected_direction_option = ""
    st.session_state.custom_direction_option = ""
    st.session_state.route_generation_notice = ""
    st.session_state.workflow_run_id = ""
    st.session_state.app_state_initialized = True

if "route_result" not in st.session_state:
    st.session_state.route_result = None

if "user_goal" not in st.session_state:
    st.session_state.user_goal = ""

if "blockage_result" not in st.session_state:
    st.session_state.blockage_result = None

if "followup_question" not in st.session_state:
    st.session_state.followup_question = ""

if "followup_answer" not in st.session_state:
    st.session_state.followup_answer = ""

if "last_followup_answer" not in st.session_state:
    st.session_state.last_followup_answer = ""

if "effective_goal" not in st.session_state:
    st.session_state.effective_goal = ""

if "is_waiting_followup" not in st.session_state:
    st.session_state.is_waiting_followup = False

if "need_direction_choice" not in st.session_state:
    st.session_state.need_direction_choice = False

if "direction_options" not in st.session_state:
    st.session_state.direction_options = []

if "selected_direction_option" not in st.session_state:
    st.session_state.selected_direction_option = ""

if "custom_direction_option" not in st.session_state:
    st.session_state.custom_direction_option = ""

if "route_generation_notice" not in st.session_state:
    st.session_state.route_generation_notice = ""

if "workflow_run_id" not in st.session_state:
    st.session_state.workflow_run_id = ""


with st.sidebar:
    if st.button("清空当前结果"):
        st.session_state.user_goal = ""
        st.session_state.route_result = None
        st.session_state.blockage_result = None
        st.session_state.followup_question = ""
        st.session_state.followup_answer = ""
        st.session_state.last_followup_answer = ""
        st.session_state.effective_goal = ""
        st.session_state.is_waiting_followup = False
        clear_direction_choice_state()
        st.session_state.route_generation_notice = ""
        st.session_state.workflow_run_id = ""
        clear_app_state()
        st.rerun()


st.header("第一步：生成完整路线")

user_goal = st.text_input(
    "请输入你的目标",
    value=st.session_state.user_goal,
    placeholder="例如：AI 动漫短剧"
)

if st.button("生成路线", type="primary"):
    if not user_goal.strip():
        st.warning("请先输入用户目标。")
    else:
        st.session_state.route_generation_notice = ""
        clear_direction_choice_state()
        with st.spinner("正在生成路线，请稍候..."):
            try:
                app = build_route_workflow()
                final_state = app.invoke({
                    "user_goal": user_goal.strip()
                })
                st.session_state.workflow_run_id = final_state.get("workflow_run_id", "")

                error_message = final_state.get("error_message", "")
                if error_message:
                    st.error(error_message)
                else:
                    route_result = final_state.get("route_result")
                    if route_result:
                        st.session_state.user_goal = user_goal.strip()
                        st.session_state.route_result = route_result
                        st.session_state.blockage_result = None
                        st.session_state.followup_question = ""
                        st.session_state.followup_answer = ""
                        st.session_state.last_followup_answer = ""
                        st.session_state.effective_goal = final_state.get("effective_goal", "") or ""
                        st.session_state.is_waiting_followup = False
                        clear_direction_choice_state()
                        st.session_state.route_generation_notice = ""
                        save_app_state(
                            user_goal=st.session_state.user_goal,
                            route_result=st.session_state.route_result,
                            blockage_result=None,
                        )
                        st.success("路线生成完成。")
                    elif final_state.get("need_followup") and final_state.get("followup_question"):
                        st.session_state.user_goal = user_goal.strip()
                        st.session_state.route_result = None
                        st.session_state.blockage_result = None
                        st.session_state.followup_question = final_state.get("followup_question", "")
                        st.session_state.followup_answer = ""
                        st.session_state.last_followup_answer = ""
                        st.session_state.effective_goal = ""
                        st.session_state.is_waiting_followup = True
                        clear_direction_choice_state()
                        st.session_state.route_generation_notice = ""
                        save_app_state(
                            user_goal=st.session_state.user_goal,
                            route_result=None,
                            blockage_result=None,
                        )
                        st.info("当前信息还不够，先补充一点信息再继续生成路线。")
                    else:
                        st.error("未生成 route_result，请检查工作流输出。")

            except Exception as e:
                st.exception(e)


if st.session_state.is_waiting_followup:
    st.info("当前信息还不够，先补充一点信息再继续生成路线。")
    st.write(f"**原始目标：** {st.session_state.user_goal}")
    st.write(st.session_state.followup_question)

    followup_answer = st.text_input(
        "请补充信息",
        value=st.session_state.followup_answer,
        placeholder="例如：我想做 AI 动漫短剧"
    )

    if st.button("提交补充信息并继续生成路线", type="primary"):
        if not followup_answer.strip():
            st.warning("补充信息不能为空，请先回答补问后再继续生成路线。")
        else:
            with st.spinner("正在继续生成路线，请稍候..."):
                try:
                    app = build_route_workflow()
                    final_state = app.invoke({
                        "user_goal": st.session_state.user_goal,
                        "followup_answer": followup_answer.strip(),
                    })
                    st.session_state.workflow_run_id = final_state.get("workflow_run_id", "")

                    error_message = final_state.get("error_message", "")
                    if error_message:
                        st.error(error_message)
                    else:
                        route_result = final_state.get("route_result")
                        if (
                            final_state.get("close_result") == "close_partial"
                            and final_state.get("need_direction_choice")
                        ):
                            st.session_state.route_result = None
                            st.session_state.blockage_result = None
                            st.session_state.followup_question = ""
                            st.session_state.followup_answer = followup_answer.strip()
                            st.session_state.last_followup_answer = followup_answer.strip()
                            st.session_state.effective_goal = ""
                            st.session_state.is_waiting_followup = False
                            st.session_state.need_direction_choice = True
                            st.session_state.direction_options = final_state.get("direction_options", [])
                            st.session_state.selected_direction_option = (
                                st.session_state.direction_options[0]
                                if st.session_state.direction_options
                                else ""
                            )
                            st.session_state.custom_direction_option = ""
                            st.session_state.route_generation_notice = (
                                "你补充的信息已经能判断大方向，但还缺少生成高质量路线的关键细节。"
                                "请选择一个更具体的方向继续。"
                            )
                            save_app_state(
                                user_goal=st.session_state.user_goal,
                                route_result=None,
                                blockage_result=None,
                            )
                            st.info(st.session_state.route_generation_notice)
                            st.rerun()
                        elif route_result:
                            close_result = final_state.get("close_result", "")
                            effective_goal = final_state.get("effective_goal", "")
                            submitted_followup_answer = followup_answer.strip()

                            st.session_state.route_result = route_result
                            st.session_state.blockage_result = None
                            st.session_state.followup_question = ""
                            st.session_state.followup_answer = submitted_followup_answer
                            st.session_state.last_followup_answer = submitted_followup_answer
                            st.session_state.effective_goal = effective_goal
                            st.session_state.is_waiting_followup = False
                            clear_direction_choice_state()
                            st.session_state.route_generation_notice = ""

                            if close_result == "close_failed":
                                st.session_state.route_generation_notice = (
                                    "你补充的信息仍不足以支撑高质量定制路线，"
                                    "系统已基于保底方向生成一条最小起步路线。"
                                )
                            save_app_state(
                                user_goal=st.session_state.user_goal,
                                route_result=st.session_state.route_result,
                                blockage_result=None,
                            )
                            st.success("路线生成完成。")
                            st.rerun()
                        else:
                            st.error("未生成 route_result，请检查工作流输出。")

                except Exception as e:
                    st.exception(e)


if st.session_state.need_direction_choice:
    st.info(
        "你补充的信息已经能判断大方向，但还缺少生成高质量路线的关键细节。"
        "请选择一个更具体的方向继续。"
    )
    direction_options = st.session_state.direction_options or []

    if direction_options:
        selected_direction = st.radio(
            "请选择更具体的方向",
            options=direction_options,
        )
    else:
        selected_direction = ""
        st.warning("当前没有可用方向选项，请在下面输入一个更具体的方向。")

    st.text_input(
        "如果以上都不合适，请补充一个更具体的方向",
        key="custom_direction_option",
        placeholder="例如：做一套小红书文案生成流程，能批量出标题、正文和封面文案",
    )

    if st.button("使用该方向继续生成路线", type="primary"):
        custom_direction = st.session_state.custom_direction_option.strip()
        final_direction = custom_direction or selected_direction

        if not final_direction.strip():
            st.warning("请先选择或填写一个更具体的方向。")
        else:
            st.session_state.selected_direction_option = final_direction.strip()
            with st.spinner("正在按你选择的方向生成路线，请稍候..."):
                try:
                    app = build_route_workflow()
                    final_state = app.invoke({
                        "user_goal": st.session_state.user_goal,
                        "followup_answer": final_direction.strip(),
                    })
                    st.session_state.workflow_run_id = final_state.get("workflow_run_id", "")

                    error_message = final_state.get("error_message", "")
                    if error_message:
                        st.error(error_message)
                    else:
                        route_result = final_state.get("route_result")
                        if route_result:
                            st.session_state.route_result = route_result
                            st.session_state.blockage_result = None
                            st.session_state.followup_question = ""
                            st.session_state.followup_answer = final_direction.strip()
                            st.session_state.last_followup_answer = final_direction.strip()
                            st.session_state.effective_goal = final_state.get(
                                "effective_goal",
                                final_direction.strip(),
                            )
                            st.session_state.is_waiting_followup = False
                            clear_direction_choice_state()
                            st.session_state.route_generation_notice = ""
                            save_app_state(
                                user_goal=st.session_state.user_goal,
                                route_result=st.session_state.route_result,
                                blockage_result=None,
                            )
                            st.success("路线生成完成。")
                            st.rerun()
                        elif (
                            final_state.get("close_result") == "close_partial"
                            and final_state.get("need_direction_choice")
                        ):
                            st.session_state.direction_options = final_state.get("direction_options", [])
                            st.session_state.need_direction_choice = True
                            st.warning("这个方向仍然偏泛，请再选择或补充得更具体一点。")
                            st.rerun()
                        else:
                            st.error("未生成 route_result，请检查工作流输出。")

                except Exception as e:
                    st.exception(e)


if (
    st.session_state.route_result is not None
    and not st.session_state.is_waiting_followup
    and not st.session_state.need_direction_choice
):
    if st.session_state.route_generation_notice:
        st.info(st.session_state.route_generation_notice)

    render_route_result(st.session_state.route_result)

    st.divider()
    st.header("第二步：卡点细化")

    step_options = [
        step.step_name for step in st.session_state.route_result.steps
    ]

    selected_step = st.selectbox(
        "请选择你卡住的步骤",
        options=step_options
    )

    blockage_text = st.text_area(
        "请描述你卡住的原因",
        placeholder="例如：角色图不稳定，人物每次都不一样"
    )

    if st.button("细化卡点"):
        if not selected_step.strip() or not blockage_text.strip():
            st.warning("请先选择步骤，并填写卡点描述。")
        else:
            with st.spinner("正在分析卡点，请稍候..."):
                try:
                    app = build_blockage_workflow()
                    final_state = app.invoke({
                        "user_goal": st.session_state.user_goal,
                        "effective_goal": st.session_state.get("effective_goal", ""),
                        "followup_answer": st.session_state.get(
                            "last_followup_answer",
                            st.session_state.get("followup_answer", ""),
                        ),
                        "route_result": st.session_state.get("route_result"),
                        "selected_step": selected_step.strip(),
                        "blockage_text": blockage_text.strip(),
                    })
                    st.session_state.workflow_run_id = final_state.get("workflow_run_id", "")

                    error_message = final_state.get("error_message", "")
                    if error_message:
                        st.error(error_message)
                    else:
                        blockage_result = final_state.get("blockage_result")
                        if blockage_result:
                            st.session_state.blockage_result = blockage_result
                            save_app_state(
                                user_goal=st.session_state.user_goal,
                                route_result=st.session_state.route_result,
                                blockage_result=st.session_state.blockage_result,
                            )
                            st.success("卡点细化完成。")
                        else:
                            st.error("未生成 blockage_result，请检查工作流输出。")

                except Exception as e:
                    st.exception(e)

    if st.session_state.blockage_result is not None:
        st.divider()
        render_blockage_result(st.session_state.blockage_result)

    st.divider()
    render_observability_panel()
