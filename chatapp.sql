-- Bảng Người dùng (Users)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    avatar_url TEXT
);

-- Bảng Cuộc trò chuyện (Conversations)
CREATE TABLE conversations (
    conversation_id SERIAL PRIMARY KEY,
    conversation_name VARCHAR(255),
    conversation_type VARCHAR(20) NOT NULL
);

-- Bảng Thành viên cuộc trò chuyện (Conversation Members)
CREATE TABLE conversation_members (
    conversation_id INTEGER REFERENCES conversations(conversation_id),
    user_id INTEGER REFERENCES users(user_id),
    PRIMARY KEY (conversation_id, user_id)
);

-- Bảng Tin nhắn (Messages)
CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(conversation_id),
    sender_id INTEGER REFERENCES users(user_id),
    message_text TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Trạng thái tin nhắn (Message Status)
CREATE TABLE message_status (
    message_id INTEGER REFERENCES messages(message_id),
    user_id INTEGER REFERENCES users(user_id),
    status VARCHAR(20) NOT NULL,
    PRIMARY KEY (message_id, user_id)
);

-- Bảng Tệp đính kèm (Attachments)
CREATE TABLE attachments (
    attachment_id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES messages(message_id),
    attachment_url TEXT NOT NULL,
    attachment_type VARCHAR(50) NOT NULL
);
