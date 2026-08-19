const SECURITY_HEADERS: Readonly<Record<string, string>> = {
  "Content-Security-Policy": [
    "default-src 'none'",
    "base-uri 'none'",
    "connect-src 'none'",
    "form-action 'none'",
    "frame-ancestors 'none'",
    "img-src 'self' data:",
    "manifest-src 'self'",
    "script-src 'none'",
    "style-src 'unsafe-inline'"
  ].join("; "),
  "Permissions-Policy": [
    "accelerometer=()",
    "ambient-light-sensor=()",
    "autoplay=()",
    "camera=()",
    "display-capture=()",
    "encrypted-media=()",
    "fullscreen=()",
    "geolocation=()",
    "gyroscope=()",
    "magnetometer=()",
    "microphone=()",
    "midi=()",
    "payment=()",
    "picture-in-picture=()",
    "publickey-credentials-get=()",
    "usb=()",
    "xr-spatial-tracking=()"
  ].join(", "),
  "Referrer-Policy": "no-referrer",
  "X-Content-Type-Options": "nosniff"
};

export function withSecurityHeaders(init?: HeadersInit): Headers {
  const headers = new Headers(init);

  for (const [name, value] of Object.entries(SECURITY_HEADERS)) {
    headers.set(name, value);
  }

  return headers;
}
