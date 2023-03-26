import os
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, \
    ConversationHandler

from src.commands import start, help_command, airport, countries_list, airports_list, airport_info, echo

AIRPORTS, AIRPORT_INFO = range(2)


def build_bot():
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start),
                      CommandHandler("help", help_command),
                      CommandHandler("airport", airport),
                      CommandHandler("airports", countries_list)],
        states={
            AIRPORTS: [CallbackQueryHandler(airports_list)],
            AIRPORT_INFO: [CallbackQueryHandler(airport_info)]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # on different commands - answer in Telegram
    application.add_handler(conv_handler)

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    return application


async def start_webhook(application):
    port = int(os.getenv("BOT_WEBHOOK_PORT"))

    async def telegram(request: Request) -> Response:
        await application.update_queue.put(
            Update.de_json(data=await request.json(), bot=application.bot)
        )
        return Response()

    starlette_app = Starlette(
        routes=[
            Route("/telegram", telegram, methods=["POST"])
        ]
    )

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=starlette_app,
            port=port,
            use_colors=False,
            host="127.0.0.1",
        )
    )

    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()


def start_pooling(application):
    application.run_polling()