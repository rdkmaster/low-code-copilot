import React from 'react';
import { ProChat } from '@ant-design/pro-chat';

// 将请求函数拆分出来单独定义
const handleChatRequest = async (messages) => {
  const url = "http://localhost:8000/chat";
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream'
    },
    body: JSON.stringify({messages})
  });
  // 确保服务器响应是成功的
  if (!response.ok || !response.body) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  // 获取 reader
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  const encoder = new TextEncoder();

  const readableStream = new ReadableStream({
    async start(controller) {
      function push() {
        reader
          .read()
          .then(({ done, value }) => {
            if (done) {
              controller.close();
              return;
            }
            const chunk = decoder.decode(value, { stream: true });
            const messages = chunk.split('data:').map(i => i.trim()).filter(i => !!i && i !== '[DONE]');
            messages.forEach(message => {
              controller.enqueue(encoder.encode(message));
            });
            push();
          });
      }
      push();
    },
  });
  return new Response(readableStream);
};

const App = () => (
  <ProChat
    style={{
      height: '100vh',
      width: '100vw',
    }}
    helloMessage={
      '欢迎使用低代码助手，我是[《说透低代码》](https://time.geekbang.org/column/intro/100108401)专栏的AI演示助手。'
    }
    request={handleChatRequest}
  />
);

export default App;
