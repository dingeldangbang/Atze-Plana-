package de.atze.plana;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.*;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Native Core workspace. Real API records only; no device or agent executor. */
public final class MainActivity extends Activity {
    public static final int SERVER_ID = 1001, TOKEN_ID = 1002, CONNECT_ID = 1003, STATUS_ID = 1004;
    public static final int DISCONNECT_ID = 1005, WORKSPACE_ID = 1006;
    private ExecutorService worker;
    private EditText server, token;
    private TextView status, selection;
    private Button connect, disconnect;
    private LinearLayout workspace, content;
    private AlertDialog confirmation;
    private String sessionOrigin, sessionToken, selectedProject;
    private volatile int generation;
    private boolean busy;

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private TextView label(LinearLayout parent, String text, int size) {
        TextView view = new TextView(this); view.setText(text); view.setTextSize(size);
        view.setTextColor(0xff182c39); view.setPadding(0, dp(8), 0, dp(8));
        view.setSaveEnabled(false); parent.addView(view); return view;
    }
    private Button button(LinearLayout parent, String text, Runnable action) {
        Button view = new Button(this); view.setText(text); view.setAllCaps(false);
        parent.addView(view); view.setOnClickListener(v -> action.run()); return view;
    }
    private EditText field(LinearLayout parent, String hint, int max, boolean multiline) {
        EditText view = new EditText(this); view.setHint(hint); view.setSaveEnabled(false);
        view.setImportantForAutofill(View.IMPORTANT_FOR_AUTOFILL_NO_EXCLUDE_DESCENDANTS);
        view.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS
            | (multiline ? InputType.TYPE_TEXT_FLAG_MULTI_LINE : 0));
        view.setSingleLine(!multiline); view.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(max)});
        parent.addView(view); return view;
    }
    private LinearLayout column(LinearLayout parent) {
        LinearLayout view = new LinearLayout(this); view.setOrientation(LinearLayout.VERTICAL);
        if (parent != null) parent.addView(view); return view;
    }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        worker = Executors.newSingleThreadExecutor();
        ScrollView scroll = new ScrollView(this); scroll.setFillViewport(true);
        LinearLayout root = column(null); root.setPadding(dp(20), dp(12), dp(20), dp(24));
        root.setBackgroundColor(0xfff4f7f8); scroll.addView(root); setContentView(scroll);
        // targetSdk 35 is edge-to-edge: don't place controls behind status/navigation bars.
        scroll.setOnApplyWindowInsetsListener((view, insets) -> {
            view.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom()); return insets;
        });
        label(root, "ATZE PLANA", 28);
        label(root, "Core Workspace · 0.2-dev\nProjekte · Aufgaben · PLAN-Status", 16);
        label(root, "Entwicklung, keine Vollplattform. Nur eigenen HTTPS-Core autorisieren. Dieser erhält Token und Eingaben. Token bleibt nur während dieser sichtbaren Sitzung im RAM; Hintergrundwechsel trennt. Keine Geräte-, Repair- oder Agentensteuerung.", 14);
        server = field(root, "HTTPS-Serveradresse ohne Pfad", 2048, false); server.setId(SERVER_ID);
        server.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        token = field(root, "Operator- oder Reviewer-Token", 4096, false); token.setId(TOKEN_ID);
        token.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        connect = button(root, "Diesen HTTPS-Core für diese Sitzung autorisieren", this::connect); connect.setId(CONNECT_ID);
        disconnect = button(root, "Trennen und lokale Anzeige leeren", () -> clearSession("NOT CONNECTED · Sitzung beendet.")); disconnect.setId(DISCONNECT_ID);
        status = label(root, "NOT CONNECTED · Keine Daten geladen.", 14); status.setId(STATUS_ID);
        workspace = column(root); workspace.setId(WORKSPACE_ID); workspace.setVisibility(View.GONE);
        selection = label(workspace, "Kein Projekt ausgewählt.", 14);
        button(workspace, "Projekte laden", () -> list("projects", 0));
        button(workspace, "Projekt anlegen (Operator)", this::projectForm);
        button(workspace, "Aufgaben laden", () -> list("tasks", 0));
        button(workspace, "Aufgabe anlegen (Operator)", this::taskForm);
        button(workspace, "PLAN-Verzeichnis laden", () -> list("plans", 0));
        content = column(workspace);
    }
    private interface Job { String run(String origin, String credential) throws Exception; }
    private interface Display { void show(String response) throws Exception; }
    private void enable(View view, boolean enabled) {
        view.setEnabled(enabled);
        if (view instanceof ViewGroup) for (int i = 0; i < ((ViewGroup) view).getChildCount(); i++) enable(((ViewGroup) view).getChildAt(i), enabled);
    }
    private void busy(boolean value) {
        busy = value; connect.setEnabled(!value && sessionToken == null);
        server.setEnabled(!value && sessionToken == null); token.setEnabled(!value && sessionToken == null);
        enable(workspace, !value);
    }
    private void connect() {
        if (busy) return;
        final String origin = server.getText().toString().trim();
        final String credential = token.getText().toString(); token.setText("");
        try { ExternalDataGateway.validateOrigin(origin); }
        catch (Exception error) { status.setText("BLOCKED · gültiger HTTPS-Origin ohne Pfad erforderlich."); return; }
        run(origin, credential, false, (url, key) -> ExternalDataGateway.runtime(url, key), response -> {
            sessionOrigin = origin; sessionToken = credential;
            workspace.setVisibility(View.VISIBLE); status.setText(response);
        });
    }
    private void run(String origin, String credential, boolean mutation, Job job, Display display) {
        final int current = generation; busy(true);
        status.setText("UNBEKANNT · Anfrage läuft. Keine automatische Wiederholung.");
        worker.execute(() -> {
            if (current != generation) return;
            String response = null; String failure = null;
            try { response = job.run(origin, credential); }
            catch (ExternalDataGateway.CoreHttpException error) {
                failure = "HTTP " + error.status + " · " + (error.status == 401 ? "Token ungültig." : error.status == 403 ? "Rolle nicht berechtigt." : error.status == 409 ? "Zustandskonflikt; aktuellen Core-Stand prüfen." : "Anfrage nicht erfolgreich.");
            } catch (Exception error) { failure = "TLS, Netzwerk, Eingabe oder Antwort ungültig. Keine Ersatzdaten."; }
            final String output = response, problem = failure;
            runOnUiThread(() -> {
                if (current != generation || isDestroyed() || isFinishing()) return;
                try {
                    if (problem != null) {
                        content.removeAllViews(); status.setText("BLOCKED / UNAVAILABLE · " + problem
                            + (mutation ? "\nSpeicherergebnis möglicherweise unbekannt. Vor erneutem Senden Liste prüfen; kein automatischer Retry." : ""));
                    } else {
                        status.setText("Antwort vom autorisierten Core erhalten. Keine Geräteausführung."); display.show(output);
                    }
                } catch (Exception invalid) {
                    content.removeAllViews(); status.setText("UNAVAILABLE · Antwort entspricht nicht dem erwarteten Core-Vertrag."
                        + (mutation ? " Speicherergebnis unbekannt; vor Wiederholung Liste prüfen." : ""));
                } finally { busy(false); }
            });
        });
    }
    private void api(String method, String path, JSONObject body, Display display) {
        if (busy || sessionToken == null) return;
        run(sessionOrigin, sessionToken, "POST".equals(method),
            (origin, credential) -> ExternalDataGateway.request(origin, credential, method, path, body), display);
    }
    private void selectProject(String id) {
        selectedProject = id; selection.setText("Ausgewähltes Projekt: " + id);
    }
    private void list(String kind, int offset) {
        content.removeAllViews();
        api("GET", "/api/" + kind + "?limit=20&offset=" + offset, null, response -> {
            JSONArray rows = new JSONArray(response);
            // Validate the entire page before presenting any record.
            if (rows.length() > 20) throw new IllegalStateException("PAGE_LIMIT");
            for (int i = 0; i < rows.length(); i++) {
                JSONObject row = rows.getJSONObject(i); CoreRequests.id(row.getString("id"));
                if (kind.equals("projects")) { row.getString("name"); row.getString("description"); }
                else if (kind.equals("tasks")) { row.getString("title"); row.getString("action"); CoreRequests.id(row.getString("project_id")); }
                else { CoreRequests.id(row.getString("task_id")); CoreRequests.id(row.getString("project_id")); }
            }
            label(content, kind + " · Einträge ab " + (offset + 1) + " · Workspace-weit", 20);
            if (rows.length() == 0) label(content, "Keine Einträge auf dieser Seite.", 16);
            for (int i = 0; i < rows.length(); i++) {
                JSONObject row = rows.getJSONObject(i); final String id = row.getString("id");
                if (kind.equals("projects")) {
                    label(content, row.getString("name") + "\n" + row.getString("description") + "\nID: " + id, 16);
                    button(content, "Dieses Projekt auswählen", () -> selectProject(id));
                } else if (kind.equals("tasks")) {
                    label(content, row.getString("title") + "\nDeklarierte Aktion: " + row.getString("action")
                        + "\nProjekt: " + row.getString("project_id") + "\nAufgabe: " + id, 16);
                    button(content, "Triage anfordern (Audit-Eintrag, keine Ausführung)", () -> confirm("Triage anfordern", "Aufgabe: " + id + "\nDer Core prüft den aktuellen Stand und schreibt einen Audit-Eintrag. Keine Freigabe oder Ausführung.",
                        () -> { content.removeAllViews(); api("POST", "/api/tasks/" + id + "/triage", null, result -> {
                            JSONObject decision = new JSONObject(result);
                            if (decision.getBoolean("executed")) throw new IllegalStateException("UNEXPECTED_EXECUTION");
                            label(content, "Triage · " + decision.getString("state") + "\nValidierung: " + decision.getString("validation_status"), 20);
                            label(content, decision.toString(2), 14);
                        }); }));
                } else {
                    label(content, "PLAN: " + id + "\nAufgabe: " + row.getString("task_id") + "\nProjekt: " + row.getString("project_id"), 16);
                    button(content, "Aktuellen Context-Lock-Status prüfen", () -> {
                        content.removeAllViews(); api("GET", "/api/plans/" + id + "/status", null, result -> {
                            JSONObject state = new JSONObject(result);
                            if (state.getBoolean("allowed_for_action")) throw new IllegalStateException("UNEXPECTED_PERMISSION");
                            label(content, "PLAN · " + state.getString("state"), 20);
                            label(content, state.toString(2) + "\nCURRENT bedeutet Kontextbindung, nicht Wahrheit oder Ausführungsrecht.", 14);
                        });
                    });
                }
            }
            if (offset > 0) button(content, "Vorherige Seite", () -> list(kind, offset - 20));
            if (rows.length() == 20 && offset <= 999999960) button(content, "Nächste Seite", () -> list(kind, offset + 20));
        });
    }
    private void confirm(String title, String detail, Runnable submit) {
        if (busy || sessionToken == null) return;
        confirmation = new AlertDialog.Builder(this).setTitle(title).setMessage("Ziel: " + sessionOrigin + "\n\n" + detail)
            .setNegativeButton("Abbrechen", null).setPositiveButton("An Core senden", (dialog, which) -> {
                if (sessionToken != null && !busy) submit.run();
            }).create();
        confirmation.show(); confirmation.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
    }
    private void projectForm() {
        content.removeAllViews(); label(content, "Projekt anlegen · Operator", 20);
        EditText name = field(content, "Projektname (1–120 Zeichen)", 120, false);
        EditText description = field(content, "Beschreibung (optional)", 2000, true);
        button(content, "Eingaben prüfen und bestätigen", () -> {
            try {
                JSONObject body = CoreRequests.project(name.getText().toString(), description.getText().toString());
                confirm("Projekt anlegen", body.toString(2), () -> api("POST", "/api/projects", body, response -> {
                    JSONObject row = new JSONObject(response); String id = CoreRequests.id(row.getString("id"));
                    row.getString("name"); selectProject(id); content.removeAllViews();
                    label(content, "Projekt gespeichert · " + id + "\n" + row.getString("name"), 18);
                }));
            } catch (Exception error) { status.setText("BLOCKED · Projektname erforderlich; Feldgrenzen beachten."); }
        });
    }
    private void taskForm() {
        content.removeAllViews(); label(content, "Aufgabe anlegen · Operator", 20);
        label(content, "Ein Registereintrag, kein ausführbarer Befehl. Auch READ benötigt Evidenz und Challenge. Keine automatische Freigabe.", 14);
        EditText project = field(content, "Projekt-ID (aus Projektliste)", 36, false);
        if (selectedProject != null) project.setText(selectedProject);
        EditText title = field(content, "Aufgabentitel", 200, false);
        Spinner action = new Spinner(this); action.setSaveEnabled(false);
        action.setAdapter(new ArrayAdapter<String>(this, android.R.layout.simple_spinner_dropdown_item, CoreRequests.ACTIONS)); content.addView(action);
        EditText evidence = field(content, "Vorhandene Evidenz-IDs, mit Komma getrennt (optional)", 2000, true);
        CheckBox conditions = new CheckBox(this); conditions.setSaveEnabled(false);
        conditions.setText("Ich bestätige die Voraussetzungen (keine technische Verifikation)"); content.addView(conditions);
        button(content, "Eingaben prüfen und bestätigen", () -> {
            try {
                JSONObject body = CoreRequests.task(project.getText().toString(), title.getText().toString(),
                    action.getSelectedItem().toString(), evidence.getText().toString(), conditions.isChecked());
                confirm("Aufgabe registrieren, nicht ausführen", body.toString(2), () -> api("POST", "/api/tasks", body, response -> {
                    JSONObject row = new JSONObject(response); String id = CoreRequests.id(row.getString("id"));
                    row.getString("title"); content.removeAllViews();
                    label(content, "Aufgabe gespeichert · " + id + "\nKeine Triage, Freigabe oder Ausführung ausgelöst.", 18);
                }));
            } catch (Exception error) { status.setText("BLOCKED · Projekt-ID, Titel und eindeutige Evidenz-IDs prüfen (maximal 50)."); }
        });
    }
    private void clearSession(String message) {
        generation++; sessionToken = null; sessionOrigin = null; selectedProject = null;
        if (confirmation != null) { confirmation.dismiss(); confirmation = null; }
        token.setText(""); content.removeAllViews(); selection.setText("Kein Projekt ausgewählt.");
        workspace.setVisibility(View.GONE); status.setText(message); busy(false);
    }
    @Override public void onStop() {
        clearSession("NOT CONNECTED · Hintergrundwechsel beendet die Sitzung; Anzeige und Entwürfe geleert. Bereits gesendete Anfragen können nicht zurückgerufen werden.");
        super.onStop();
    }
    @Override public void onDestroy() { generation++; worker.shutdownNow(); token.setText(""); super.onDestroy(); }
}
