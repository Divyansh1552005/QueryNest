# Chat History Management

## Overview

QueryNest now supports intelligent chat history management when resuming sessions. This feature gives you control over previous conversations without affecting your knowledge base (FAISS vectors).

---

## How It Works

### Session States

#### 1. **New Session** (No previous data)
- App starts normally
- No menu shown
- Fresh chat begins immediately

#### 2. **Resumed Session WITHOUT Chat History**
- FAISS vectors loaded from disk
- No previous conversation exists
- No menu shown
- Fresh chat begins immediately

#### 3. **Resumed Session WITH Chat History** ⭐
- FAISS vectors loaded from disk
- Previous conversation exists in `chat.json`
- **One-time menu is shown** with three options

---

## The Menu

When you resume a session that has previous conversations, you'll see:

```
────────────────────────────────────────────────────────────
📚 This session has 8 previous message(s)
────────────────────────────────────────────────────────────

What would you like to do?

  [1] 📜 View previous conversation
  [2] 🗑️  Start fresh chat (keep knowledge base)
  [Enter] ▶️  Continue from where you left off

Your choice:
```

### Option 1: View Previous Conversation

Shows all previous messages in a readable format:

```
============================================================
📜 PREVIOUS CONVERSATION
============================================================

👤 You: What is the main topic of this video?

🤖 Assistant: The video discusses machine learning fundamentals,
focusing on supervised learning techniques.

👤 You: Can you explain gradient descent?

🤖 Assistant: Gradient descent is an optimization algorithm...

============================================================

✅ You can now continue the conversation below.
```

**What happens:**
- All previous messages are printed
- Chat history is **preserved**
- You can continue the conversation with context

---

### Option 2: Start Fresh Chat

Clears all previous conversations while keeping your knowledge base intact.

**Confirmation prompt:**
```
⚠️  Are you sure? This will delete chat history. (y/N):
```

**If you confirm (y):**
```
✅ Chat history cleared (vectors preserved)
✅ Starting fresh! Your knowledge base is still intact.
```

**What happens:**
- `chat.json` is deleted
- Chat memory is cleared
- FAISS vectors are **preserved** (your documents are still searchable)
- You start with a clean slate for questions

**If you cancel (N or Enter):**
```
❌ Cancelled. Chat history preserved.
```

---

### Option 3: Continue (Default)

Just press **Enter** to continue without viewing or clearing.

```
✅ Continuing from previous session.
```

**What happens:**
- Previous chat context is maintained
- No messages printed to console
- LLM will have access to conversation history for context
- You continue exactly where you left off

---

## Architecture

### Separation of Concerns

The implementation cleanly separates three concerns:

#### 1. **Data Management** (`ChatMemory`)
```python
# src/memory/chat_memory.py
class ChatMemory:
    def has_previous_chats() -> bool      # Check existence
    def get_chat_count() -> int           # Count messages
    def clear_chat_history()              # Delete chat.json
    def print_previous_chats()            # Display messages
```

#### 2. **User Interaction** (`chat_menu`)
```python
# src/memory/chat_menu.py
def should_show_menu(session_exists, chat_memory) -> bool
    # Determines if menu should appear

def show_chat_history_menu(chat_memory) -> None
    # Handles user interaction and delegates to ChatMemory
```

#### 3. **Application Flow** (`app.py`)
```python
# Integrated into session resume flow
memory = ChatMemory(session_id)

if should_show_menu(session_exists, memory):
    show_chat_history_menu(memory)  # One-time only!

# Continue with chat loop...
```

---

## Important Constraints

### ✅ What This Feature Does

- Shows menu **once per app start** for resumed sessions with chat history
- Allows viewing previous conversations
- Allows clearing chat while preserving vectors
- Keeps presentation logic separate from data logic

### 🚫 What This Feature Does NOT Do

- Does NOT modify session IDs
- Does NOT affect FAISS vectors or embeddings
- Does NOT change session metadata
- Does NOT appear in the chat loop (only at startup)
- Does NOT automatically print old chats without consent

---

## File Structure

```
~/.querynest/
└── sessions/
    └── <session_id>/
        ├── vectors.faiss        # FAISS index (preserved)
        ├── vectors.pkl          # FAISS metadata (preserved)
        ├── meta.json            # Session info (preserved)
        └── chat.json            # Chat history (can be cleared)
```

**Key insight:** Only `chat.json` is affected by the "Start fresh" option. All other files remain untouched.

---

## Usage Examples

### Example 1: Resume and Continue

```bash
$ python app.py
Choose source (yt / pdf / web): yt
Enter YouTube URL: https://youtube.com/watch?v=ABC123
Enter session name: ML Tutorial

🔑 Session ID: a1b2c3d4...
✅ Session resumed from disk
📝 Session: ML Tutorial

────────────────────────────────────────────────────────────
📚 This session has 6 previous message(s)
────────────────────────────────────────────────────────────

What would you like to do?

  [1] 📜 View previous conversation
  [2] 🗑️  Start fresh chat (keep knowledge base)
  [Enter] ▶️  Continue from where you left off

Your choice: [Press Enter]

✅ Continuing from previous session.

💬 Chat started! Ask questions (type 'exit' to quit)

You: Tell me more about neural networks
```

---

### Example 2: View Previous Chats

```bash
Your choice: 1

============================================================
📜 PREVIOUS CONVERSATION
============================================================

👤 You: What is machine learning?

🤖 Assistant: Machine learning is a subset of artificial
intelligence that enables systems to learn from data...

👤 You: What are the main types?

🤖 Assistant: The three main types are: 1) Supervised
Learning, 2) Unsupervised Learning, 3) Reinforcement Learning...

============================================================

✅ You can now continue the conversation below.

💬 Chat started! Ask questions (type 'exit' to quit)

You: Can you elaborate on supervised learning?
```

---

### Example 3: Start Fresh

```bash
Your choice: 2

⚠️  Are you sure? This will delete chat history. (y/N): y

✅ Chat history cleared (vectors preserved)
✅ Starting fresh! Your knowledge base is still intact.

💬 Chat started! Ask questions (type 'exit' to quit)

You: What is the video about?
Assistant: [Answers based on vectors, no chat context]
```

---

## Benefits

### 🎯 **User Control**
- You decide what to do with old chats
- No forced viewing or clearing
- Simple, clear options

### 🚀 **Performance**
- Menu shown only once (not in every loop iteration)
- No automatic printing of long conversations
- Efficient memory usage

### 🏗️ **Clean Architecture**
- Presentation separate from data
- Easy to test and maintain
- No coupling between chat and vectors

### 🔒 **Data Integrity**
- FAISS vectors always preserved
- Session metadata always preserved
- Only chat history can be cleared

---

## Technical Details

### Menu Trigger Logic

```python
def should_show_menu(session_exists: bool, chat_memory) -> bool:
    """
    Menu is shown ONLY when:
    1. Session exists (resumed, not new)
    2. Chat history has messages
    """
    return session_exists and chat_memory.has_previous_chats()
```

### Execution Flow

```
User starts app
    ↓
Collect source metadata
    ↓
Compute session_id
    ↓
Check if FAISS exists
    ↓
    ├─ NO (New Session)
    │   ↓
    │   Fetch → Split → Build FAISS
    │   ↓
    │   Initialize empty ChatMemory
    │   ↓
    │   No menu (no history)
    │
    └─ YES (Resumed Session)
        ↓
        Load FAISS from disk
        ↓
        Initialize ChatMemory (loads chat.json)
        ↓
        Check if chat.json has messages?
        ↓
        ├─ NO → No menu, start chat
        │
        └─ YES → Show one-time menu ⭐
            ↓
            [1] View → Print → Continue
            [2] Clear → Delete chat.json → Continue
            [Enter] → Continue
            ↓
Start chat loop
```

---

## Code Reference

### Key Files

- **`src/memory/chat_memory.py`**: Core chat data operations
- **`src/memory/chat_menu.py`**: User interaction logic
- **`src/memory/__init__.py`**: Module exports
- **`app.py`**: Integration point (lines ~200-208)

### Key Functions

```python
# Check if menu should appear
should_show_menu(session_exists, memory) -> bool

# Show the interactive menu
show_chat_history_menu(memory) -> None

# ChatMemory methods
memory.has_previous_chats() -> bool
memory.get_chat_count() -> int
memory.print_previous_chats() -> None
memory.clear_chat_history() -> None
```

---

## Testing

### Test Case 1: New Session
**Expected:** No menu appears, chat starts immediately

### Test Case 2: Resumed Session, No History
**Expected:** No menu appears, chat starts immediately

### Test Case 3: Resumed Session, With History + View
**Expected:** Menu appears → choose 1 → see previous chats → continue

### Test Case 4: Resumed Session, With History + Clear
**Expected:** Menu appears → choose 2 → confirm → chat.json deleted → vectors intact

### Test Case 5: Resumed Session, With History + Continue
**Expected:** Menu appears → press Enter → continue with context

---

## Future Enhancements

Possible improvements for future versions:

- [ ] Export chat history to file
- [ ] Search through old conversations
- [ ] Show chat statistics (total messages, tokens, etc.)
- [ ] Archive old chats instead of deleting
- [ ] Import chat history from another session

---

## FAQ

**Q: What happens if I accidentally clear chat history?**
A: Your knowledge base (FAISS vectors) is preserved, so you can still ask questions about your documents. Only the conversation context is lost.

**Q: Can I recover deleted chat history?**
A: No, clearing is permanent. The feature asks for confirmation to prevent accidents.

**Q: Does clearing chats free up disk space?**
A: Yes, but chat.json is typically small (<100KB). FAISS vectors use more space and are preserved.

**Q: Will the LLM remember previous chats after clearing?**
A: No, the LLM only has access to what's in chat.json. Clearing removes all context.

**Q: Can I skip the menu and go straight to chat?**
A: Yes, just press Enter when the menu appears.

**Q: Does the menu slow down startup?**
A: No, it's a simple check and only adds ~50ms to startup time.

---

## Summary

The chat history management feature provides a clean, user-friendly way to handle previous conversations when resuming sessions. It respects user choice, maintains separation of concerns, and never interferes with the underlying knowledge base.

**Key Principle:** Your documents (vectors) are permanent. Your conversations (chat) are flexible.