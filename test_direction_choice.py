from graph.direction_options import (
    build_direction_options,
    detect_bucket,
)
from graph.nodes import close_followup_node
from graph.workflow import build_route_workflow


def test_detect_bucket():
    assert detect_bucket("", "小红书") == "content"
    assert detect_bucket("", "背单词") == "learning"
    assert detect_bucket("", "分镜") == "shortdrama"
    assert detect_bucket("", "AI 视频") == "shortdrama"
    assert detect_bucket("", "公众号") == "content"


def test_build_direction_options_keyword_priority():
    xiaohongshu_options = build_direction_options("content", "我想做内容", "小红书")
    assert len(xiaohongshu_options) == 3
    assert all("小红书" in option for option in xiaohongshu_options)

    word_options = build_direction_options("learning", "我想学习", "背单词")
    assert len(word_options) == 3
    assert "背单词" in word_options[0]

    storyboard_options = build_direction_options("shortdrama", "我想做 AI 视频", "分镜")
    assert len(storyboard_options) == 3
    assert any("分镜" in option or "镜头" in option for option in storyboard_options[:2])

    default_options = build_direction_options("learning", "", "", limit=3)
    assert len(default_options) == 3
    assert default_options[0].startswith("做 7 天英语学习计划")


def test_close_partial_stops_for_direction_choice():
    app = build_route_workflow()
    final_state = app.invoke({
        "user_goal": "我想做内容",
        "followup_answer": "小红书",
    })

    assert final_state.get("close_result") == "close_partial"
    assert final_state.get("need_direction_choice") is True
    assert final_state.get("direction_options")
    assert final_state.get("route_result") is None
    assert final_state.get("current_stage") == "direction_choice_required"


def test_close_success_not_affected():
    state = close_followup_node({
        "user_goal": "我想做内容",
        "followup_answer": "做一套小红书文案生成流程，能批量出标题、正文和封面文案",
    })

    assert state.get("close_result") == "close_success"
    assert state.get("need_direction_choice") is False
    assert state.get("effective_goal") == "做一套小红书文案生成流程，能批量出标题、正文和封面文案"


def test_close_failed_keeps_failed_result():
    state = close_followup_node({
        "user_goal": "做项目",
        "followup_answer": "随便做点AI的",
    })

    assert state.get("close_result") == "close_failed"
    assert state.get("need_direction_choice") is False


def test_pure_generic_answer_goes_close_failed():
    state = close_followup_node({
        "user_goal": "做项目",
        "followup_answer": "随便",
    })

    assert state.get("close_result") == "close_failed"
    assert state.get("need_direction_choice") is False


def test_generic_content_answer_goes_close_partial():
    state = close_followup_node({
        "user_goal": "我想做内容",
        "followup_answer": "随便帮我做一个小红书内容创作流程",
    })

    assert state.get("close_result") == "close_partial"
    assert state.get("need_direction_choice") is True
    assert state.get("detected_bucket") == "content"
    assert state.get("direction_options")
    assert state.get("route_result") is None


def test_generic_shortdrama_answer_goes_close_partial():
    state = close_followup_node({
        "user_goal": "我想做 AI 视频",
        "followup_answer": "你看着办，做一个 AI 视频生成流程",
    })

    assert state.get("close_result") == "close_partial"
    assert state.get("need_direction_choice") is True
    assert state.get("detected_bucket") == "shortdrama"
    assert state.get("direction_options")
    assert state.get("route_result") is None


if __name__ == "__main__":
    test_detect_bucket()
    test_build_direction_options_keyword_priority()
    test_close_partial_stops_for_direction_choice()
    test_close_success_not_affected()
    test_close_failed_keeps_failed_result()
    test_pure_generic_answer_goes_close_failed()
    test_generic_content_answer_goes_close_partial()
    test_generic_shortdrama_answer_goes_close_partial()
    print("test_direction_choice.py: all tests passed")
