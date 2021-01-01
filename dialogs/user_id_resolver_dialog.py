# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datatypes_date_time.timex import Timex

from botbuilder.core import MessageFactory
from botbuilder.dialogs import WaterfallDialog, DialogTurnResult, WaterfallStepContext
from botbuilder.dialogs.prompts import (
    NumberPrompt,
    PromptValidatorContext,
    PromptOptions
)
from botbuilder.schema import InputHints
from .cancel_and_help_dialog import CancelAndHelpDialog


class UserIDResolverDialog(CancelAndHelpDialog):
    def __init__(self, dialog_id: str = None):
        super(UserIDResolverDialog, self).__init__(
            dialog_id or UserIDResolverDialog.__name__
        )

        self.add_dialog(
            NumberPrompt(
                NumberPrompt.__name__, UserIDResolverDialog.user_id_prompt_validator
            )
        )
        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__ + "2", [self.initial_step, self.final_step]
            )
        )

        self.initial_dialog_id = WaterfallDialog.__name__ + "2"

    async def initial_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        user_id = step_context.options

        prompt_msg_text = "Please create a user ID"
        prompt_msg = MessageFactory.text(
            prompt_msg_text, prompt_msg_text, InputHints.expecting_input
        )

        reprompt_msg_text = "I'm sorry, could not book flight"
        reprompt_msg = MessageFactory.text(
            reprompt_msg_text, reprompt_msg_text, InputHints.expecting_input
        )

        if user_id is None:
            # We were not given any date at all so prompt the user.
            return await step_context.prompt(
                NumberPrompt.__name__,
                PromptOptions(prompt=prompt_msg, retry_prompt=reprompt_msg),
            )

        return await step_context.next(user_id)

    async def final_step(self, step_context: WaterfallStepContext):
        user_id = step_context.result
        return await step_context.end_dialog(user_id)

    @staticmethod
    async def user_id_prompt_validator(prompt_context: PromptValidatorContext) -> bool:
        if prompt_context.recognized.succeeded:
            return True

        return False
