import './App.css';
import { ProChat } from '@ant-design/pro-chat';
import { useTheme } from 'antd-style';
import { useState, useEffect } from 'react';
import { applyPatch } from 'fast-json-patch';
import { v4 as uuidv4 } from 'uuid';

function App() {
  const theme = useTheme();
  const [chats, setChats] = useState([]);
  const [sessionId, setSessionId] = useState(null);

  // The Page Schema, representing the single source of truth for the UI
  const [pageSchema, setPageSchema] = useState({
    pageId: "page_001",
    title: "首页",
    components: []
  });

  // Generate a unique session ID when the component mounts
  useEffect(() => {
    setSessionId(uuidv4());
  }, []);

  // The core request handler that communicates with the backend
  const handleRequest = async (messages) => {
    if (!sessionId) {
      return new Response("Error: Session ID not initialized.");
    }

    const lastMessage = messages[messages.length - 1];

    const response = await fetch('http://127.0.0.1:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: lastMessage.content,
        sessionId: sessionId,
      }),
    });

    const responseData = await response.json();

    // Case 1: Backend returns a JSON Patch to update the UI
    if (responseData.patch) {
      // Apply the patch to the current schema
      const { newDocument } = applyPatch(pageSchema, responseData.patch);
      setPageSchema(newDocument);
      // Return a confirmation message to display in the chat
      return new Response("好的，已为您更新界面。");
    }

    // Case 2: Backend returns a follow-up question or a query answer
    if (responseData.message || responseData.text) {
      return new Response(responseData.message || responseData.text);
    }

    // Fallback for any other case
    return new Response('抱歉，我遇到了一些问题，请稍后再试。');
  };

  return (
    <div className="AppLayout">
      <div className="ChatContainer"
        style={{
          background: theme.colorBgLayout,
        }}
      >
        <ProChat
          chats={chats}
          onChatsChange={(newChats) => {
            setChats(newChats);
          }}
          request={handleRequest}
        />
      </div>
      <div className="PreviewContainer">
        <h2>页面实时状态 (Page Schema)</h2>
        <pre className="SchemaDisplay">
          <code>{JSON.stringify(pageSchema, null, 2)}</code>
        </pre>
      </div>
    </div>
  );
}

export default App;