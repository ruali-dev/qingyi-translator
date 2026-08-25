/* global Zotero */
"use strict";

var PaperTranslatorConnector = (() => {
  const PLUGIN_ID = "paper-translator-connector@local";
  const ENDPOINT = "http://127.0.0.1:8765/translate";
  const SELECTION_TTL_MS = 30_000;
  let selectionHandler;
  let contextMenuHandler;
  let lastSelections = new WeakMap();

  function startup() {
    selectionHandler = ({ reader, params }) => {
      const selected = (params?.annotation?.text || params?.text || "").trim();
      if (!selected) return;
      lastSelections.set(reader, { text: selected, at: Date.now() });
    };

    contextMenuHandler = ({ reader, append }) => {
      const cached = lastSelections.get(reader);
      if (!cached || Date.now() - cached.at > SELECTION_TTL_MS) return;
      append({
        label: "翻译选中文字",
        onCommand: () => translateSelection(reader, cached.text)
      });
    };

    Zotero.Reader.registerEventListener(
      "renderTextSelectionPopup", selectionHandler, PLUGIN_ID
    );
    Zotero.Reader.registerEventListener(
      "createViewContextMenu", contextMenuHandler, PLUGIN_ID
    );
  }

  async function translateSelection(reader, text) {
    try {
      await Zotero.HTTP.request("POST", ENDPOINT, {
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
        responseType: "json",
        timeout: 65000
      });
    } catch (error) {
      Zotero.debug(`Paper Translator connector: ${error}`);
      reader._iframeWindow.alert(
        "无法连接轻译。请先运行 PaperTranslator.exe，并检查模型设置。"
      );
    }
  }

  function shutdown() {
    if (selectionHandler) {
      Zotero.Reader.unregisterEventListener("renderTextSelectionPopup", selectionHandler);
      selectionHandler = undefined;
    }
    if (contextMenuHandler) {
      Zotero.Reader.unregisterEventListener("createViewContextMenu", contextMenuHandler);
      contextMenuHandler = undefined;
    }
    lastSelections = new WeakMap();
  }

  return { startup, shutdown };
})();
