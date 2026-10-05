import asyncio

import streamlit as st
from sqlalchemy import select

from app.core.security import hash_password, verify_password
from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.db.models import Conversation, Document, Message, User
from app.langgraph.workflow import run_chat_workflow
from app.rag.retriever import ingest_document


st.set_page_config(
    page_title="Mini AI Engineering Platform",
    page_icon="AI",
    layout="wide",
)

async def register_user(
    email: str,
    password: str,
):
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(User).where(User.email == email)
            )

            existing_user = result.scalar_one_or_none()

            if existing_user:
                return None, "Email already registered."

            user = User(
                email=email,
                password_hash=hash_password(password),
            )

            db.add(user)

            await db.commit()
            await db.refresh(user)

            return user, None

        except Exception as error:
            await db.rollback()
            return None, str(error)

async def login_user(
    email: str,
    password: str,
):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == email)
        )

        user = result.scalar_one_or_none()

        if user is None:
            return None

        if not verify_password(
            password,
            user.password_hash,
        ):
            return None

        return user


async def get_or_create_conversation(
    user_id: int,
) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user_id
            )
            .order_by(
                Conversation.created_at.desc()
            )
        )

        conversation = result.scalars().first()

        if conversation:
            return conversation.id

        conversation = Conversation(
            user_id=user_id,
        )

        db.add(conversation)

        await db.commit()
        await db.refresh(conversation)

        return conversation.id


async def create_new_conversation(
    user_id: int,
) -> int:
    async with AsyncSessionLocal() as db:
        conversation = Conversation(
            user_id=user_id,
        )

        db.add(conversation)

        await db.commit()
        await db.refresh(conversation)

        return conversation.id


async def get_messages(
    conversation_id: int,
):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Message)
            .where(
                Message.conversation_id
                == conversation_id
            )
            .order_by(
                Message.created_at.asc()
            )
        )

        return result.scalars().all()


async def upload_document(
    user_id: int,
    filename: str,
    content_type: str,
    file_bytes: bytes,
):
    async with AsyncSessionLocal() as db:
        document = Document(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
        )

        db.add(document)

        await db.flush()

        chunk_count = await ingest_document(
            db=db,
            document_id=document.id,
            file_bytes=file_bytes,
        )

        return document.id, chunk_count


async def ask_question(
    conversation_id: int,
    question: str,
):
    async with AsyncSessionLocal() as db:
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=question,
        )

        db.add(user_message)

        await db.commit()

        answer = await run_chat_workflow(
            question=question,
            conversation_id=conversation_id,
            db=db,
        )

        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
        )

        db.add(assistant_message)

        await db.commit()

        return answer


if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None


st.title("Mini AI Engineering Platform")

st.caption(
    "Document intelligence with RAG, PostgreSQL, "
    "conversation memory, and LangGraph."
)


if st.session_state.user_id is None:
    st.sidebar.header("Account")

    account_mode = st.sidebar.radio(
        "Choose action",
        ["Login", "Register"],
    )

    email = st.sidebar.text_input(
        "Email",
        placeholder="you@example.com",
    )

    password = st.sidebar.text_input(
        "Password",
        type="password",
    )

    if account_mode == "Register":
        if st.sidebar.button(
            "Create account",
            use_container_width=True,
        ):
            if not email or not password:
                st.sidebar.error(
                    "Email and password are required."
                )
            else:
                user, error = asyncio.run(
                    register_user(
                        email=email,
                        password=password,
                    )
                )

                if error:
                    st.sidebar.error(error)
                else:
                    st.sidebar.success(
                        "Account created. You can now log in."
                    )

    else:
        if st.sidebar.button(
            "Login",
            use_container_width=True,
        ):
            if not email or not password:
                st.sidebar.error(
                    "Email and password are required."
                )
            else:
                user = asyncio.run(
                    login_user(
                        email=email,
                        password=password,
                    )
                )

                if user is None:
                    st.sidebar.error(
                        "Invalid email or password."
                    )
                else:
                    st.session_state.user_id = user.id
                    st.session_state.user_email = user.email
                    st.session_state.conversation_id = (
                        asyncio.run(
                            get_or_create_conversation(
                                user.id
                            )
                        )
                    )

                    st.rerun()

    st.info(
        "Register or log in from the sidebar to use the platform."
    )

    st.stop()


with st.sidebar:
    st.success(
        f"Logged in as {st.session_state.user_email}"
    )

    if st.button(
        "New conversation",
        use_container_width=True,
    ):
        st.session_state.conversation_id = (
            asyncio.run(
                create_new_conversation(
                    st.session_state.user_id
                )
            )
        )

        st.rerun()

    if st.button(
        "Log out",
        use_container_width=True,
    ):
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.conversation_id = None

        st.rerun()

    st.divider()

    st.header("Documents")

    uploaded_file = st.file_uploader(
        "Upload a PDF",
        type=["pdf"],
    )

    if uploaded_file is not None:
        if st.button(
            "Process PDF",
            use_container_width=True,
        ):
            with st.spinner(
                "Extracting, chunking, and embedding..."
            ):
                try:
                    document_id, chunk_count = asyncio.run(
                        upload_document(
                            user_id=st.session_state.user_id,
                            filename=uploaded_file.name,
                            content_type=uploaded_file.type,
                            file_bytes=uploaded_file.getvalue(),
                        )
                    )

                    if chunk_count == 0:
                        st.error(
                            "No readable text was found in this PDF."
                        )
                    else:
                        st.success(
                            f"Processed {chunk_count} chunks."
                        )

                except Exception as error:
                    st.error(
                        f"Document processing failed: {error}"
                    )

    st.divider()

    if settings.openai_api_key:
        st.success("OpenAI key detected")
    else:
        st.error("OpenAI key missing")


st.header("Chat")

messages = asyncio.run(
    get_messages(
        st.session_state.conversation_id
    )
)

for message in messages:
    with st.chat_message(message.role):
        st.markdown(message.content)


question = st.chat_input(
    "Ask something about your documents..."
)

if question:
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = asyncio.run(
                    ask_question(
                        conversation_id=(
                            st.session_state.conversation_id
                        ),
                        question=question,
                    )
                )

                st.markdown(answer)

            except Exception as error:
                st.error(
                    f"AI request failed: {error}"
                )