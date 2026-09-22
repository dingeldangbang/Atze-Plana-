package de.atze.plana;

import org.json.JSONArray;
import org.json.JSONObject;

/** Bounded payloads for existing Core contracts, not an action executor. */
public final class CoreRequests {
    public static final String[] ACTIONS = {"read", "write", "flash", "firmware", "edl_write", "production_deploy", "payment"};
    public static String text(String value, int max) {
        String clean = value.trim();
        if (clean.isEmpty() || clean.length() > max) throw new IllegalArgumentException("INVALID_FIELD_LENGTH");
        return clean;
    }
    public static String id(String value) {
        String clean = value.trim();
        if (!clean.matches("[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}")) throw new IllegalArgumentException("INVALID_CORE_ID");
        return clean;
    }
    public static JSONObject project(String name, String description) throws Exception {
        if (description.trim().length() > 2000) throw new IllegalArgumentException("DESCRIPTION_TOO_LONG");
        return new JSONObject().put("name", text(name, 120)).put("description", description.trim());
    }
    public static JSONObject task(String project, String title, String action, String references, boolean preconditions) throws Exception {
        boolean allowed = false;
        for (String candidate : ACTIONS) if (candidate.equals(action)) allowed = true;
        if (!allowed) throw new IllegalArgumentException("UNKNOWN_ACTION");
        JSONArray evidence = new JSONArray();
        java.util.HashSet<String> unique = new java.util.HashSet<>();
        if (!references.trim().isEmpty()) {
            for (String reference : references.trim().split("[,\\s]+")) {
                String key = id(reference);
                if (!unique.add(key) || unique.size() > 50) throw new IllegalArgumentException("INVALID_EVIDENCE_REFERENCES");
                evidence.put(key);
            }
        }
        return new JSONObject().put("project_id", id(project)).put("title", text(title, 200))
            .put("action", action).put("evidence_ids", evidence).put("preconditions_met", preconditions);
    }
    private CoreRequests() { }
}
