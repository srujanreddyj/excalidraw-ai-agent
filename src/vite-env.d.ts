/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_PYTHON_AGENT_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
