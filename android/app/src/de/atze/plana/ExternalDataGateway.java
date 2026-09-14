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

/** Only implemented Android outbound path: explicit authenticated HTTPS Core read. */
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
    public static String runtime(String origin, String token) throws Exception {
        URI uri = validateOrigin(origin);
        if (token.length() < 32 || token.contains("\r") || token.contains("\n")) {
            throw new IllegalArgumentException("VALID_TOKEN_REQUIRED");
        }
        HttpsURLConnection connection = (HttpsURLConnection) uri.resolve("/api/runtime").toURL().openConnection();
        connection.setSSLSocketFactory(tlsFactory());
        connection.setInstanceFollowRedirects(false);
        connection.setConnectTimeout(10000);
        connection.setReadTimeout(10000);
        // Android 8+ system TLS/CA/hostname verification. Never install trust-all callbacks.
        connection.setRequestProperty("Authorization", "Bearer " + token);
        connection.setRequestProperty("Accept", "application/json");
        try {
            int status = connection.getResponseCode();
            if (status != 200) throw new IllegalStateException("HTTP_" + status + "_NO_FALLBACK");
            ByteArrayOutputStream result = new ByteArrayOutputStream();
            try (InputStream stream = connection.getInputStream()) {
                byte[] bytes = new byte[1024];
                int count;
                while ((count = stream.read(bytes)) != -1) {
                    if (result.size() + count > 16384) throw new IllegalStateException("RESPONSE_LIMIT");
                    result.write(bytes, 0, count);
                }
            }
            JSONObject data = new JSONObject(result.toString("UTF-8"));
            String mode = data.getString("mode");
            if (!"operational".equals(mode) && !"test".equals(mode)) throw new IllegalStateException("UNKNOWN_MODE");
            return "Core-Modus: " + mode + "\nDatenbereich: " + data.getString("data_scope")
                + "\nProduktionsstatus: " + data.getString("production_readiness")
                + "\nChallenge Worker: " + data.getString("challenge_worker")
                + "\nNur Status gelesen. Keine Ausführung oder Freigabe.";
        } finally { connection.disconnect(); }
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
