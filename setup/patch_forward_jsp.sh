#!/usr/bin/env bash
# patch_forward_jsp.sh
# Patches forward.jsp inside the running OSCAR container so that the
# case_program_id session attribute is always set before the eChart loads.
# Without this patch, opening an eChart directly throws NumberFormatException.

set -e

CONTAINER="${1:-oscar-lab-oscar}"
JSP="/usr/local/tomcat/webapps/oscar/casemgmt/forward.jsp"
WORK_DIR="/usr/local/tomcat/work/Catalina/localhost/oscar/org/apache/jsp/casemgmt"

echo "→ Patching forward.jsp in container: $CONTAINER"

# Check already patched
if docker exec "$CONTAINER" grep -q "case_program_id fallback" "$JSP" 2>/dev/null; then
    echo "  Already patched — skipping."
    exit 0
fi

# Apply patch: inject case_program_id session fallback before existing logic
docker exec "$CONTAINER" sed -i \
  's|    String useNewCaseMgmt;|    // case_program_id fallback (oscar-emr-lab patch)\n    String _cpid = request.getParameter("case_program_id");\n    if (_cpid != null \&\& _cpid.length() > 0) { session.setAttribute("case_program_id", _cpid); }\n    else if (session.getAttribute("case_program_id") == null) { session.setAttribute("case_program_id", "10034"); }\n    String useNewCaseMgmt;|' \
  "$JSP"

# Delete compiled JSP cache so Tomcat recompiles on next request
docker exec "$CONTAINER" rm -f \
  "${WORK_DIR}/forward_jsp.class" \
  "${WORK_DIR}/forward_jsp.java" 2>/dev/null || true

echo "  ✓ forward.jsp patched and cache cleared."
