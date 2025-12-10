from src.bot.state_machine import IntakeStateMachine, State


def test_full_dialog_flow_reaches_close():
    machine = IntakeStateMachine(chat_id="chat-1", max_total_responses=15)

    response = machine.start()
    assert response.state == State.CASE_DESCRIPTION

    response = machine.handle_user_reply("There is overdue credit card debt")
    assert response.state == State.DEBT_DETAILS

    response = machine.handle_user_reply("Credit card and a small microloan")
    assert response.state == State.CITY

    response = machine.handle_user_reply("Springfield")
    assert response.state == State.DOCS_INFO

    response = machine.handle_user_reply("Contract and bank letters")
    assert response.state == State.CONTACTS

    response = machine.handle_user_reply(
        "Alex Smith, @alex_s", summary_builder=lambda ctx: "Summary placeholder"
    )
    assert response.state == State.CONFIRMATION
    assert "Summary" in response.reply_text or "summary" in response.reply_text.lower()

    response = machine.handle_user_reply("yes")
    assert response.state == State.CLOSE
    assert response.should_save is True
