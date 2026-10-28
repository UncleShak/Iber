// desktop/src/main/env.d.ts
// Ambient types for the main-process build.

// Vite "?raw" imports (license public key, section 3.11).
declare module "*?raw" {
  const content: string;
  export default content;
}
