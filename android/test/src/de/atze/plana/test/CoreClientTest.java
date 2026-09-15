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
import de.atze.plana.CoreRequests;
import org.json.JSONObject;

/** Real installed-app tests, no synthetic server/model/device provider. */
public final class CoreClientTest extends Instrumentation {
    @Override public void onCreate(Bundle arguments) { super.onCreate(arguments); start(); }
    private interface Invalid { void run() throws Exception; }
    private void reject(Invalid action) throws Exception {
        try { action.run(); } catch (IllegalArgumentException expected) { return; }
        throw new AssertionError("Unsafe input accepted");
    }
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
                if (activity.findViewById(MainActivity.WORKSPACE_ID).getVisibility() != android.view.View.GONE) throw new AssertionError("Unauthenticated workspace visible");
                token.setText("synthetic-lifecycle-input-not-a-credential");
                callActivityOnStop(activity);
                if (token.length() != 0) throw new AssertionError("Background token retained");
                if (!status.getText().toString().contains("NOT CONNECTED")) throw new AssertionError("Background session retained");
                ((Button) activity.findViewById(MainActivity.DISCONNECT_ID)).performClick();
                if (activity.findViewById(MainActivity.WORKSPACE_ID).getVisibility() != android.view.View.GONE) throw new AssertionError("Disconnected workspace visible");
                activity.finish();
            });
            String[] forbidden = {"http://example.com", "https://user:password@example.com", "https://example.com/path", "https://example.com/?q=private", "https://example.com/#fragment", "https://example.com:0", "https://example.com:65536"};
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
            String key = "00000000-0000-4000-8000-000000000001"; // synthetic payload validation only
            JSONObject project = CoreRequests.project("  Isolated contract input  ", " description ");
            if (!project.getString("name").equals("Isolated contract input")) throw new AssertionError("Project normalization");
            for (String action : CoreRequests.ACTIONS) {
                JSONObject task = CoreRequests.task(key, "Task input", action, "", false);
                if (task.getBoolean("preconditions_met") || task.getJSONArray("evidence_ids").length() != 0) throw new AssertionError("Invented prerequisites");
                if (!task.getString("action").equals(action)) throw new AssertionError("Action altered");
            }
            if (CoreRequests.task(key, "Task", "read", key, true).getJSONArray("evidence_ids").length() != 1) throw new AssertionError("Evidence lost");
            reject(() -> CoreRequests.project("   ", ""));
            reject(() -> CoreRequests.task(key, "Task", "execute", "", false));
            reject(() -> CoreRequests.task("../projects", "Task", "read", "", false));
            reject(() -> CoreRequests.task(key, "Task", "read", key + "," + key, false));
            reject(() -> CoreRequests.id("00000000000000000000000000000000"));
            for (String collection : new String[]{"projects", "tasks", "plans"}) {
                ExternalDataGateway.validateRoute("GET", "/api/" + collection + "?limit=20&offset=0");
                ExternalDataGateway.validateRoute("GET", "/api/" + collection + "?limit=20&offset=20");
            }
            ExternalDataGateway.validateRoute("POST", "/api/projects");
            ExternalDataGateway.validateRoute("POST", "/api/tasks");
            ExternalDataGateway.validateRoute("POST", "/api/tasks/" + key + "/triage");
            ExternalDataGateway.validateRoute("GET", "/api/plans/" + key + "/status");
            for (String path : new String[]{"//example.com/api/projects", "/api/tasks/" + key + "/approve", "/api/control/stop", "/api/projects?limit=20&offset=-1", "/api/projects?limit=20&offset=0&extra=secret", "/api/projects/../tasks"}) {
                reject(() -> ExternalDataGateway.validateRoute("GET", path));
                reject(() -> ExternalDataGateway.validateRoute("POST", path));
            }
            reject(() -> ExternalDataGateway.request("https://example.com", "short", "GET", "/api/runtime", null));
            reject(() -> ExternalDataGateway.request("https://example.com", "synthetic-invalid-token-with-newline\n", "GET", "/api/runtime", null));
            result.putString("atze_result", "PASS");
            result.putString("scope", "actual installed app launch, empty state, session lifecycle clearing, unsafe origins/routes/token rejection, project/task JSON contracts, TLS protocols; no live Core exchange or hardware test");
            finish(Activity.RESULT_OK, result);
        } catch (Throwable error) {
            result.putString("atze_result", "FAIL"); result.putString("error_type", error.getClass().getSimpleName());
            finish(Activity.RESULT_CANCELED, result);
        }
    }
}
