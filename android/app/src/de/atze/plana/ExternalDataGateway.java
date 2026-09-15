package de.atze.plana;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.URI;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.SSLSocketFactory;
import java.net.Socket;
import java.net.InetAddress;
import java.io.IOException;
import java.util.ArrayList;
import org.json.JSONObject;

/** Only Android outbound path: consent-bound HTTPS, fixed Core routes, no fallback. */
public final class ExternalDataGateway {
    public static URI validateOrigin(String value) throws Exception {
        URI uri = new URI(value.trim());
        if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost() == null
                || uri.getUserInfo() != null || uri.getRawQuery() != null || uri.getRawFragment() != null
                || (uri.getRawPath() != null && !uri.getRawPath().isEmpty() && !"/".equals(uri.getRawPath()))
                || uri.getPort() == 0 || uri.getPort() > 65535) {
            throw new IllegalArgumentException("HTTPS_ORIGIN_REQUIRED");
        }
        return uri;
    }
    public static void validateRoute(String method, String path) {
        boolean read = "GET".equals(method) && (
            path.equals("/api/runtime")
            || path.matches("/api/(projects|tasks|plans)\\?limit=20&offset=[0-9]{1,9}")
            || path.matches("/api/plans/[a-f0-9-]{36}/status"));
        boolean write = "POST".equals(method) && (
            path.equals("/api/projects") || path.equals("/api/tasks")
            || path.matches("/api/tasks/[a-f0-9-]{36}/triage"));
        if (!read && !write) throw new IllegalArgumentException("CORE_ROUTE_DENIED");
    }
    public static String request(String origin, String token, String method, String path, JSONObject body) throws Exception {
        URI uri = validateOrigin(origin);
        validateRoute(method, path);
        if (token == null || token.length() < 32 || token.length() > 4096 || !token.matches("[!-~]+")) {
            throw new IllegalArgumentException("VALID_TOKEN_REQUIRED");
        }
        if ("GET".equals(method) && body != null) throw new IllegalArgumentException("GET_BODY_DENIED");
        byte[] payload = body == null ? new byte[0] : body.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
        if (payload.length > 65536) throw new IllegalArgumentException("REQUEST_LIMIT");
        HttpsURLConnection connection = (HttpsURLConnection) uri.resolve(path).toURL().openConnection();
        try {
            connection.setSSLSocketFactory(tlsFactory());
            connection.setInstanceFollowRedirects(false);
            connection.setUseCaches(false);
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(10000);
            connection.setRequestMethod(method);
            // System CA and hostname verification; never install trust-all callbacks.
            connection.setRequestProperty("Authorization", "Bearer " + token);
            connection.setRequestProperty("Accept", "application/json");
            if ("POST".equals(method)) {
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                connection.setFixedLengthStreamingMode(payload.length);
                try (java.io.OutputStream output = connection.getOutputStream()) { output.write(payload); }
            }
            int status = connection.getResponseCode();
            int expected = "POST".equals(method) && (path.equals("/api/projects") || path.equals("/api/tasks")) ? 201 : 200;
            if (status != expected) throw new CoreHttpException(status);
            String type = connection.getContentType();
            if (type == null || !"application/json".equalsIgnoreCase(type.split(";", 2)[0].trim())) {
                throw new IllegalStateException("JSON_REQUIRED");
            }
            ByteArrayOutputStream result = new ByteArrayOutputStream();
            long deadline = android.os.SystemClock.elapsedRealtime() + 30000;
            try (InputStream stream = connection.getInputStream()) {
                byte[] bytes = new byte[4096];
                int count;
                while ((count = stream.read(bytes)) != -1) {
                    if (android.os.SystemClock.elapsedRealtime() > deadline) throw new IOException("RESPONSE_DEADLINE");
                    if (result.size() + count > 262144) throw new IllegalStateException("RESPONSE_LIMIT");
                    result.write(bytes, 0, count);
                }
            }
            return result.toString("UTF-8");
        } finally { connection.disconnect(); }
    }
    public static final class CoreHttpException extends IOException {
        public final int status;
        CoreHttpException(int status) { super("HTTP_" + status); this.status = status; }
    }
    public static String runtime(String origin, String token) throws Exception {
        JSONObject data = new JSONObject(request(origin, token, "GET", "/api/runtime", null));
        String mode = data.getString("mode");
        if (!"operational".equals(mode) && !"test".equals(mode)) throw new IllegalStateException("UNKNOWN_MODE");
        return "Core-Modus: " + mode + "\nDatenbereich: " + data.getString("data_scope")
            + "\nProduktionsstatus: " + data.getString("production_readiness")
            + "\nChallenge Worker: " + data.getString("challenge_worker")
            + "\nKeine Geräteausführung. Freigabe ist keine Ausführung.";
    }
    public static SSLSocketFactory tlsFactory() throws Exception {
        SSLContext context = SSLContext.getInstance("TLS");
        context.init(null, null, null); // system trust, never trust-all
        final SSLSocketFactory delegate = context.getSocketFactory();
        return new SSLSocketFactory() {
            private Socket secure(Socket socket) {
                SSLSocket tls = (SSLSocket) socket;
                ArrayList<String> protocols = new ArrayList<>();
                for (String name : tls.getSupportedProtocols()) {
                    if ("TLSv1.2".equals(name) || "TLSv1.3".equals(name)) protocols.add(name);
                }
                if (protocols.isEmpty()) throw new IllegalStateException("TLS12_REQUIRED");
                tls.setEnabledProtocols(protocols.toArray(new String[0])); return tls;
            }
            public String[] getDefaultCipherSuites() { return delegate.getDefaultCipherSuites(); }
            public String[] getSupportedCipherSuites() { return delegate.getSupportedCipherSuites(); }
            public Socket createSocket() throws IOException { return secure(delegate.createSocket()); }
            public Socket createSocket(Socket s, String host, int port, boolean close) throws IOException { return secure(delegate.createSocket(s, host, port, close)); }
            public Socket createSocket(String host, int port) throws IOException { return secure(delegate.createSocket(host, port)); }
            public Socket createSocket(String host, int port, InetAddress local, int localPort) throws IOException { return secure(delegate.createSocket(host, port, local, localPort)); }
            public Socket createSocket(InetAddress host, int port) throws IOException { return secure(delegate.createSocket(host, port)); }
            public Socket createSocket(InetAddress host, int port, InetAddress local, int localPort) throws IOException { return secure(delegate.createSocket(host, port, local, localPort)); }
        };
    }
    private ExternalDataGateway() { }
}
