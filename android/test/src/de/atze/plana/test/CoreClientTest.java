package de.atze.plana.test;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import de.atze.plana.MainActivity;
import de.atze.plana.ExternalDataGateway;

/** Real installed-app tests, no synthetic server/model/device provider. */
public final class CoreClientTest extends Instrumentation {
    @Override public void onCreate(Bundle arguments) { super.onCreate(arguments); start(); }
    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            Activity activity = startActivitySync(new Intent(Intent.ACTION_MAIN).setClassName("de.atze.plana", "de.atze.plana.MainActivity").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            runOnMainSync(() -> {
                TextView status = activity.findViewById(MainActivity.STATUS_ID);
                if (!status.getText().toString().contains("NOT CONNECTED")) throw new AssertionError("Invented initial connection");
                EditText url = activity.findViewById(MainActivity.SERVER_ID);
                EditText token = activity.findViewById(MainActivity.TOKEN_ID);
                url.setText("http://192.0.2.1"); token.setText("synthetic-test-input-not-a-real-token");
                ((Button) activity.findViewById(MainActivity.CONNECT_ID)).performClick();
                if (!status.getText().toString().contains("BLOCKED")) throw new AssertionError("Plaintext origin allowed");
                if (token.length() != 0) throw new AssertionError("Input token retained");
                activity.finish();
            });
            String[] forbidden = {"http://example.com", "https://user:password@example.com", "https://example.com/path", "https://example.com/?q=private"};
            for (String url : forbidden) {
                boolean rejected = false;
                try { ExternalDataGateway.validateOrigin(url); } catch (Exception expected) { rejected = true; }
                if (!rejected) throw new AssertionError("Unsafe origin accepted");
            }
            ExternalDataGateway.validateOrigin("https://example.com"); // validation only, no network call
            try (javax.net.ssl.SSLSocket socket = (javax.net.ssl.SSLSocket) ExternalDataGateway.tlsFactory().createSocket()) {
                for (String protocol : socket.getEnabledProtocols()) {
                    if (!"TLSv1.2".equals(protocol) && !"TLSv1.3".equals(protocol)) throw new AssertionError("Legacy TLS enabled");
                }
            }
            result.putString("atze_result", "PASS");
            result.putString("scope", "actual installed app launch, initial empty state, HTTP/unsafe-origin block, token clearing; no device bridge or live Core connection tested");
            finish(Activity.RESULT_OK, result);
        } catch (Throwable error) {
            result.putString("atze_result", "FAIL"); result.putString("error_type", error.getClass().getSimpleName());
            finish(Activity.RESULT_CANCELED, result);
        }
    }
}
