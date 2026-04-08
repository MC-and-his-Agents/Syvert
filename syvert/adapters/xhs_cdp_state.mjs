const [url, timeoutMsArg, cdpBaseUrlArg, sourceNoteIdArg] = process.argv.slice(2);

if (!url) {
  console.error("missing url");
  process.exit(1);
}

const timeoutMs = Number.parseInt(timeoutMsArg || "10000", 10);
const cdpBaseUrl = (cdpBaseUrlArg || "http://127.0.0.1:9222").replace(/\/$/, "");
const sourceNoteId = sourceNoteIdArg || "";
const cookieHeader = process.env.SYVERT_XHS_COOKIE_HEADER || "";
const userAgent = process.env.SYVERT_XHS_USER_AGENT || "";
const pollIntervalMs = 500;

async function main() {
  const version = await fetch(`${cdpBaseUrl}/json/version`).then((response) => {
    if (!response.ok) {
      throw new Error(`cdp_version_http_${response.status}`);
    }
    return response.json();
  });
  const browserWsUrl = version.webSocketDebuggerUrl;
  if (typeof browserWsUrl !== "string" || !browserWsUrl) {
    throw new Error("missing_browser_ws_url");
  }

  const ws = new WebSocket(browserWsUrl);
  const pending = new Map();
  let messageId = 0;
  let sessionId = null;
  let targetId = null;

  function send(method, params = {}, currentSessionId = sessionId) {
    return new Promise((resolve, reject) => {
      const id = ++messageId;
      pending.set(id, { resolve, reject });
      const payload = { id, method, params };
      if (currentSessionId) {
        payload.sessionId = currentSessionId;
      }
      ws.send(JSON.stringify(payload));
    });
  }

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (!message.id || !pending.has(message.id)) {
      return;
    }
    const { resolve, reject } = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) {
      reject(new Error(JSON.stringify(message.error)));
      return;
    }
    resolve(message.result);
  };

  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = reject;
  });

  async function evaluate(expression) {
    const result = await send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (result.exceptionDetails) {
      return undefined;
    }
    return result.result ? result.result.value : undefined;
  }

  async function evaluateJson(expression) {
    const payload = await evaluate(expression);
    if (typeof payload !== "string" || !payload) {
      return null;
    }
    try {
      return JSON.parse(payload);
    } catch {
      return null;
    }
  }

  try {
    targetId = (await send("Target.createTarget", { url: "about:blank", newWindow: false, background: true }, null))
      .targetId;
    sessionId = (await send("Target.attachToTarget", { targetId, flatten: true }, null)).sessionId;
    await send("Page.enable");
    await send("Network.enable");
    await send("Runtime.enable");
    if (userAgent) {
      await send("Network.setUserAgentOverride", { userAgent });
    }
    if (cookieHeader) {
      const cookiePairs = cookieHeader
        .split(";")
        .map((part) => part.trim())
        .filter(Boolean)
        .map((part) => {
          const index = part.indexOf("=");
          return index <= 0 ? null : { name: part.slice(0, index).trim(), value: part.slice(index + 1).trim() };
        })
        .filter(Boolean);
      for (const cookie of cookiePairs) {
        await send("Network.setCookie", { ...cookie, url: "https://www.xiaohongshu.com/" });
        await send("Network.setCookie", { ...cookie, url: "https://edith.xiaohongshu.com/" });
      }
    }
    await send("Page.navigate", { url });

    const deadline = Date.now() + Math.max(timeoutMs, pollIntervalMs);
    let keys = [];
    while (Date.now() < deadline) {
      await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
      const nextKeys = await evaluateJson(
        'window.__INITIAL_STATE__ && window.__INITIAL_STATE__.note && window.__INITIAL_STATE__.note.noteDetailMap ? JSON.stringify(Object.keys(window.__INITIAL_STATE__.note.noteDetailMap).slice(0, 20)) : null',
      );
      if (Array.isArray(nextKeys)) {
        keys = nextKeys.filter(Boolean);
        if (keys.length) {
          break;
        }
      }
    }

    if (!keys.length) {
      throw new Error("note_state_not_ready");
    }

    const currentNoteId = (await evaluate(
      'window.__INITIAL_STATE__ && window.__INITIAL_STATE__.note ? (window.__INITIAL_STATE__.note.currentNoteId || "") : ""',
    )) || "";
    const firstNoteId = (await evaluate(
      'window.__INITIAL_STATE__ && window.__INITIAL_STATE__.note ? (window.__INITIAL_STATE__.note.firstNoteId || "") : ""',
    )) || "";
    const candidates = Array.from(new Set([sourceNoteId, currentNoteId, firstNoteId, ...keys].filter(Boolean)));

    for (const key of candidates) {
      const note = await evaluateJson(`(() => {
        const root = window.__INITIAL_STATE__;
        const noteStore = root && root.note;
        const map = noteStore && noteStore.noteDetailMap;
        if (!map) return null;
        const entry = map[${JSON.stringify(key)}];
        if (!entry) return null;
        const candidate =
          (entry && entry.note) ||
          (entry && entry.note_card) ||
          (entry && entry.noteCard) ||
          entry;
        if (!candidate || !(candidate.noteId || candidate.note_id)) return null;
        const sanitizeStreamEntries = (entries) => Array.isArray(entries)
          ? entries.map((item) => ({
              masterUrl: item && (item.masterUrl || item.master_url || ""),
              master_url: item && (item.master_url || item.masterUrl || ""),
            }))
          : [];
        const sanitizeStreamGroup = (stream) => ({
          h264: sanitizeStreamEntries(stream && stream.h264),
          h265: sanitizeStreamEntries(stream && stream.h265),
          av1: sanitizeStreamEntries(stream && stream.av1),
        });
        const sanitizeImage = (image) => ({
          urlDefault: image && (image.urlDefault || image.url_default || image.url || ""),
          url: image && (image.url || image.urlPre || ""),
          livePhoto: Boolean(image && image.livePhoto),
          stream: sanitizeStreamGroup(image && image.stream),
        });
        const sanitized = {
          noteId: candidate.noteId || candidate.note_id || "",
          type: candidate.type || "",
          title: candidate.title || "",
          desc: candidate.desc || "",
          time: candidate.time || null,
          user: {
            userId: candidate.user && (candidate.user.userId || candidate.user.user_id || ""),
            nickname: candidate.user && candidate.user.nickname || "",
            avatar: candidate.user && (candidate.user.avatar || candidate.user.avatarUrl || candidate.user.image || ""),
            avatarUrl: candidate.user && (candidate.user.avatarUrl || candidate.user.avatar || candidate.user.image || ""),
            image: candidate.user && (candidate.user.image || candidate.user.avatar || candidate.user.avatarUrl || ""),
          },
          interactInfo: {
            likedCount: candidate.interactInfo && candidate.interactInfo.likedCount,
            commentCount: candidate.interactInfo && candidate.interactInfo.commentCount,
            shareCount: candidate.interactInfo && candidate.interactInfo.shareCount,
            collectedCount: candidate.interactInfo && candidate.interactInfo.collectedCount,
          },
          imageList: Array.isArray(candidate.imageList) ? candidate.imageList.map(sanitizeImage) : [],
          video: {
            consumer: {
              originVideoKey: candidate.video && candidate.video.consumer && (candidate.video.consumer.originVideoKey || candidate.video.consumer.origin_video_key || ""),
              origin_video_key: candidate.video && candidate.video.consumer && (candidate.video.consumer.origin_video_key || candidate.video.consumer.originVideoKey || ""),
            },
            media: {
              stream: sanitizeStreamGroup(candidate.video && candidate.video.media && candidate.video.media.stream),
            },
            cover: {
              urlDefault: candidate.video && candidate.video.cover && (candidate.video.cover.urlDefault || candidate.video.cover.url_default || candidate.video.cover.url || ""),
              url: candidate.video && candidate.video.cover && (candidate.video.cover.url || candidate.video.cover.urlDefault || candidate.video.cover.url_default || ""),
            },
          },
          cover: {
            urlDefault: candidate.cover && (candidate.cover.urlDefault || candidate.cover.url_default || candidate.cover.url || ""),
            url: candidate.cover && (candidate.cover.url || candidate.cover.urlDefault || candidate.cover.url_default || ""),
          },
        };
        return JSON.stringify(sanitized);
      })()`);
      if (!note || typeof note !== "object") {
        continue;
      }

      process.stdout.write(
        JSON.stringify({
          note: {
            currentNoteId,
            firstNoteId,
            noteDetailMap: {
              [key]: { note },
            },
          },
        }),
      );
      return;
    }

    throw new Error(`note_entry_not_ready:${JSON.stringify({ keys, currentNoteId, firstNoteId })}`);
  } finally {
    if (targetId) {
      try {
        await send("Target.closeTarget", { targetId }, null);
      } catch {
        // Best effort cleanup.
      }
    }
    ws.close();
  }
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exit(1);
});
