"""
Chat History Menu
-----------------
Handles one-time interactive menu when resuming sessions with existing chat history.

This module is a presentation concern - it only deals with user interaction
and delegates actual operations to ChatMemory.

Key responsibilities:
- Show menu only once per app start
- Handle user choice (view/clear/continue)
- Keep logic separate from ChatMemory data operations
"""


def show_chat_history_menu(chat_memory) -> None:
    """
    Shows one-time menu for handling existing chat history.

    This function should be called ONLY when:
    1. Session is being resumed (not new)
    2. Chat history exists (chat.json has messages)

    Args:
        chat_memory: ChatMemory instance with existing history

    Returns:
        None (modifies chat_memory state based on user choice)
    """
    message_count = chat_memory.get_chat_count()

    print("\n" + "─" * 60)
    print(f"📚 This session has {message_count} previous message(s)")
    print("─" * 60)
    print("\nWhat would you like to do?")
    print()
    print("  [1] 📜 View previous conversation")
    print("  [2] 🗑️  Start fresh chat (keep knowledge base)")
    print("  [Enter] ▶️  Continue from where you left off")
    print()

    choice = input("Your choice: ").strip()

    if choice == "1":
        # View previous chats
        chat_memory.print_previous_chats()
        print("✅ You can now continue the conversation below.\n")

    elif choice == "2":
        # Clear chat history but keep vectors
        confirm = (
            input("\n⚠️  Are you sure? This will delete chat history. (y/N): ")
            .strip()
            .lower()
        )

        if confirm == "y":
            chat_memory.clear_chat_history()
            print("✅ Starting fresh! Your knowledge base is still intact.\n")
        else:
            print("❌ Cancelled. Chat history preserved.\n")

    else:
        # Continue (default - just press Enter)
        print("✅ Continuing from previous session.\n")


def should_show_menu(session_exists: bool, chat_memory) -> bool:
    """
    Determines if the chat history menu should be shown.

    Menu is shown ONLY when:
    1. Session exists (resumed, not new)
    2. Chat history has messages

    Args:
        session_exists: True if FAISS index was loaded from disk
        chat_memory: ChatMemory instance

    Returns:
        bool: True if menu should be shown, False otherwise
    """
    return session_exists and chat_memory.has_previous_chats()
