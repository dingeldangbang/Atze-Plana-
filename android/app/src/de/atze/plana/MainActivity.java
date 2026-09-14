package de.atze.plana;

import android.app.Activity;
import android.os.Bundle;
import android.text.InputType;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Native read-only Core client. No fake devices, canned server status or embedded agent. */
public final class MainActivity extends Activity {
    public static final int SERVER_ID = 1001, TOKEN_ID = 1002, CONNECT_ID = 1003, STATUS_ID = 1004;
    private ExecutorService worker;
    private EditText server, token;
    private TextView status;
    private Button connect;
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE);
        worker = Executors.newSingleThreadExecutor();
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL); layout.setPadding(24, 60, 24, 24);
        TextView title = new TextView(this); title.setText("ATZE PLANA · Core Client\nDevelopment / Read-only"); title.setTextSize(24); layout.addView(title);
        TextView warning = new TextView(this);
        warning.setText("Nur eigenen HTTPS-Core verbinden. Dieser Server erhält den eingegebenen Token. Keine Geräte-, Repair- oder Agentensteuerung. Kein Token wird gespeichert."); layout.addView(warning);
        server = new EditText(this); server.setId(SERVER_ID); server.setHint("HTTPS-Serveradresse"); server.setSingleLine(true); server.setSaveEnabled(false); server.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI); layout.addView(server);
        token = new EditText(this); token.setId(TOKEN_ID); token.setHint("Operator- oder Reviewer-Token"); token.setSingleLine(true); token.setSaveEnabled(false); token.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD); token.setImportantForAutofill(android.view.View.IMPORTANT_FOR_AUTOFILL_NO); layout.addView(token);
        connect = new Button(this); connect.setId(CONNECT_ID); connect.setText("Diesen HTTPS-Server autorisieren und Status lesen"); layout.addView(connect);
        status = new TextView(this); status.setId(STATUS_ID); status.setSaveEnabled(false); status.setText("NOT CONNECTED · Keine Daten geladen."); layout.addView(status);
        setContentView(layout);
        connect.setOnClickListener(view -> {
            final String origin = server.getText().toString();
            final String credential = token.getText().toString(); token.setText("");
            status.setText("Status unbekannt — Verbindung wird geprüft.");
            try { ExternalDataGateway.validateOrigin(origin); }
            catch (Exception error) { status.setText("BLOCKED · gültiger HTTPS-Origin ohne Pfad erforderlich."); return; }
            connect.setEnabled(false);
            worker.execute(() -> {
                String message;
                try { message = ExternalDataGateway.runtime(origin, credential); }
                catch (Exception error) { message = "BLOCKED / UNAVAILABLE · " + error.getClass().getSimpleName() + ". Keine Ersatzdaten. Server, TLS und Berechtigung prüfen."; }
                final String output = message;
                runOnUiThread(() -> { if (!isDestroyed() && !isFinishing()) { status.setText(output); connect.setEnabled(true); } });
            });
        });
    }
    @Override public void onDestroy() { worker.shutdownNow(); token.setText(""); super.onDestroy(); }
}
