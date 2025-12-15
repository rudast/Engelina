from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram import F
from aiogram import Router
from aiogram.exceptions import TelegramAPIError
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import Command
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.types import Message
from buttons.admin import admin_answer_btns
from FSM.broadcast import BroadcastState
from middlewares.admin import AdminMiddleware
from utils import get_response


router = Router()
router.message.middleware(AdminMiddleware())


@router.message(Command('broadcast'))
async def test(msg: Message, state: FSMContext):
    await state.set_state(BroadcastState.wait_msg)
    await msg.reply('Send me message to sending to all users.')


@router.message(StateFilter(BroadcastState.wait_msg))
async def receive_broadcast_message(msg: Message, state: FSMContext, bot: Bot):
    src_chat_id = msg.chat.id
    src_message_id = msg.message_id
    is_media = bool(
        msg.photo or msg.video or msg.document or msg.animation or
        msg.audio or msg.voice,
    )

    try:
        preview_msg: Message = await bot.copy_message(
            chat_id=src_chat_id,
            from_chat_id=src_chat_id,
            message_id=src_message_id,
            reply_markup=admin_answer_btns,
        )
    except TelegramAPIError:
        logging.getLogger(__name__).exception(
            'Could not make a preview through copy_message, send the text.',
        )
        preview_msg = await bot.send_message(
            chat_id=src_chat_id,
            text='[Preview failed] Unable to display preview.',
        )
        await preview_msg.edit_reply_markup(reply_markup=admin_answer_btns)

    await state.update_data(
        src_chat_id=src_chat_id,
        src_message_id=src_message_id,
        preview_message_id=preview_msg.message_id,
        is_media=is_media,
    )

    await state.set_state(BroadcastState.confirm)


@router.callback_query(F.data == 'cancel_callback')
async def cb_bcast_cancel(
    callback: CallbackQuery, state: FSMContext,
    bot: Bot,
):
    data = await state.get_data()
    preview_id = data.get('preview_message_id')
    chat_id = callback.from_user.id

    try:
        if data.get('is_media'):
            await bot.edit_message_caption(
                chat_id=chat_id, message_id=preview_id,
                caption='❌ Broadcast cancelled.',
            )
        else:
            await bot.edit_message_text(
                chat_id=chat_id, message_id=preview_id,
                text='❌ Broadcast cancelled.',
            )
    except TelegramAPIError:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=preview_id)
        except TelegramAPIError:
            pass

    await callback.answer('❌ Broadcast cancelled.', show_alert=False)
    await state.clear()


@router.callback_query(F.data == 'confirm_callback')
async def cb_bcast_confirm(
    callback: CallbackQuery, state: FSMContext,
    bot: Bot,
):
    data = await state.get_data()
    src_chat_id = data['src_chat_id']
    src_message_id = data['src_message_id']
    preview_id = data['preview_message_id']
    is_media = data['is_media']
    admin_chat_id = callback.from_user.id

    user_ids = await get_response('http://backend:8000/users/get_users')
    user_ids = list(user_ids['users'])
    logging.getLogger(__name__).info(user_ids)

    if not user_ids:
        try:
            if is_media:
                await bot.edit_message_caption(
                    chat_id=admin_chat_id,
                    message_id=preview_id, caption='⚠️ No users to send.',
                )
            else:
                await bot.edit_message_text(
                    chat_id=admin_chat_id,
                    message_id=preview_id, text='⚠️ No users to send.',
                )
        except TelegramAPIError:
            pass
        await state.clear()
        return

    for uid in user_ids:
        try:
            await bot.copy_message(
                chat_id=uid, from_chat_id=src_chat_id,
                message_id=src_message_id,
            )
            await asyncio.sleep(0.05)
        except TelegramRetryAfter:
            logging.getLogger(__name__).warning('RetryAfter, sleeping %s')
            try:
                await bot.copy_message(
                    chat_id=uid, from_chat_id=src_chat_id,
                    message_id=src_message_id,
                )
            except Exception as ee:
                logging.getLogger(__name__).exception(
                    'Error resending to user %s: %s', uid, ee,
                )
        except Exception as e:
            logging.getLogger(__name__).info(
                'Skip user %s, reason: %s', uid, type(e).__name__,
            )

    try:
        if is_media:
            await bot.edit_message_caption(
                chat_id=admin_chat_id, message_id=preview_id,
                caption='✅ Mailing sent.',
            )
        else:
            await bot.edit_message_text(
                chat_id=admin_chat_id, message_id=preview_id,
                text='✅ Mailing sent.',
            )
    except TelegramAPIError:
        try:
            await bot.send_message(
                chat_id=admin_chat_id,
                text='✅ Mailing sent.',
            )
        except TelegramAPIError:
            pass

    await state.clear()
