function setupList({ list, $dialog, call, createToast }) {
    return {
        bulk_actions: [
            {
                label: "Bulk Email",

                onClick: async ({ selections }) => {
                    const lead_names = Array.from(selections);

                    // -------------------------------------------------
                    // STEP 1: Check selected Leads
                    // -------------------------------------------------

                    if (!lead_names.length) {
                        createToast({
                            message: "Please select at least one Lead.",
                            type: "error",
                        });

                        return;
                    }

                    // -------------------------------------------------
                    // STEP 2: Load Email Templates
                    // -------------------------------------------------

                    let templates;

                    try {
                        templates = await call("frappe.client.get_list", {
                            doctype: "Email Template",

                            fields: [
                                "name",
                                "subject",
                                "use_html",
                                "response",
                                "response_html"
                            ],

                            filters: {
                                enabled: 1,
                                reference_doctype: "CRM Lead"
                            },

                            order_by: "modified desc",

                            limit_page_length: 0
                        });

                    } catch (error) {
                        console.error(
                            "Email Template Load Error:",
                            error
                        );

                        createToast({
                            message:
                                error?.message ||
                                error?.exc ||
                                "Unable to load email templates.",

                            type: "error",
                        });

                        return;
                    }

                    if (!templates || !templates.length) {
                        createToast({
                            message:
                                "No enabled CRM Lead Email Templates found.",

                            type: "error",
                        });

                        return;
                    }

                    // -------------------------------------------------
                    // STEP 3: Template Selection
                    // -------------------------------------------------

                    let templateDialog = null;

                    const selectTemplate = (template) => {
                        if (templateDialog) {
                            templateDialog.show = false;
                            if (templateDialog.close) {
                                templateDialog.close();
                            }
                        }

                        // -----------------------------------------
                        // STEP 4: Confirmation
                        // -----------------------------------------

                        $dialog({
                                    title: "Confirm Bulk Email",

                                    message:
                                        `Send template "${template.name}" to ` +
                                        `${lead_names.length} selected Leads?`,

                                    actions: [
                                        {
                                            label: "Cancel",

                                            onClick: ({ close }) => {
                                                close();
                                            },
                                        },

                                        {
                                            label: "Send",

                                            onClick: async ({ close }) => {
                                                close();

                                                // -----------------------------------------
                                                // STEP 5: Start
                                                // -----------------------------------------

                                                createToast({
                                                    message:
                                                        "Bulk email sending started...",

                                                    type: "success",
                                                });

                                                let sent = 0;
                                                let skipped = 0;

                                                const errors = [];

                                                // -----------------------------------------
                                                // STEP 6: Get Complete Lead Documents
                                                // -----------------------------------------

                                                let leads;

                                                try {
                                                    leads =
                                                        await call(
                                                            "frappe.client.get_list",
                                                            {
                                                                doctype:
                                                                    "CRM Lead",

                                                                fields: ["*"],

                                                                filters: {
                                                                    name: [
                                                                        "in",
                                                                        lead_names
                                                                    ]
                                                                },

                                                                limit_page_length:
                                                                    lead_names.length
                                                            }
                                                        );

                                                } catch (error) {
                                                    const errorMessage =
                                                        error?.message ||
                                                        error?.exc ||
                                                        "Unable to load selected Leads.";

                                                    console.error(
                                                        "Lead Loading Error:",
                                                        error
                                                    );

                                                    createToast({
                                                        message:
                                                            `Lead loading failed: ${errorMessage}`,

                                                        type: "error",
                                                    });

                                                    return;
                                                }

                                                // -----------------------------------------
                                                // STEP 7: Process Each Lead
                                                // -----------------------------------------

                                                for (const lead of leads || []) {

                                                    // -----------------------------------------
                                                    // Check Email
                                                    // -----------------------------------------

                                                    if (!lead.email) {
                                                        skipped++;

                                                        errors.push(
                                                            `${lead.name}: No email address`
                                                        );

                                                        continue;
                                                    }

                                                    try {

                                                        // -----------------------------------------
                                                        // IMPORTANT:
                                                        // Create a template context that supports
                                                        // BOTH:
                                                        //
                                                        // {{ first_name }}
                                                        //
                                                        // AND:
                                                        //
                                                        // {{ doc.first_name }}
                                                        // -----------------------------------------

                                                        const template_context = {
                                                            ...lead,
                                                            doc: lead
                                                        };

                                                        // -----------------------------------------
                                                        // STEP 8: Render Email Template
                                                        // -----------------------------------------

                                                        const rendered =
                                                            await call(
                                                                "frappe.email.doctype.email_template.email_template.get_email_template",
                                                                {
                                                                    template_name:
                                                                        template.name,

                                                                    doc:
                                                                        template_context
                                                                }
                                                            );

                                                        const subject =
                                                            rendered?.subject ||
                                                            template.subject ||
                                                            "";

                                                        const content =
                                                            rendered?.message ||
                                                            (
                                                                template.use_html
                                                                    ? template.response_html
                                                                    : template.response
                                                            ) ||
                                                            "";

                                                        // -----------------------------------------
                                                        // Validate Subject
                                                        // -----------------------------------------

                                                        if (
                                                            !subject ||
                                                            !subject.trim()
                                                        ) {
                                                            skipped++;

                                                            errors.push(
                                                                `${lead.name}: Email subject is empty`
                                                            );

                                                            continue;
                                                        }

                                                        // -----------------------------------------
                                                        // Validate Body
                                                        // -----------------------------------------

                                                        if (
                                                            !content ||
                                                            !content.trim()
                                                        ) {
                                                            skipped++;

                                                            errors.push(
                                                                `${lead.name}: Email body is empty`
                                                            );

                                                            continue;
                                                        }

                                                        // -----------------------------------------
                                                        // STEP 9: Send Individual Email
                                                        // -----------------------------------------

                                                        await call(
                                                            "frappe.core.doctype.communication.email.make",
                                                            {
                                                                doctype:
                                                                    "CRM Lead",

                                                                name:
                                                                    lead.name,

                                                                subject:
                                                                    subject,

                                                                content:
                                                                    content,

                                                                recipients: [
                                                                    lead.email
                                                                ],

                                                                send_email: 1,

                                                                email_template:
                                                                    template.name,

                                                                raw_html:
                                                                    template.use_html
                                                                        ? 1
                                                                        : 0
                                                            }
                                                        );

                                                        // -----------------------------------------
                                                        // Successfully Sent
                                                        // -----------------------------------------

                                                        sent++;

                                                    } catch (error) {

                                                        skipped++;

                                                        const errorMessage =
                                                            error?.message ||
                                                            error?.exc ||
                                                            error?.exception ||
                                                            "Unknown email sending error";

                                                        errors.push(
                                                            `${lead.name} (${lead.email}): ${errorMessage}`
                                                        );

                                                        console.error(
                                                            `Bulk Email Error for ${lead.name}:`,
                                                            error
                                                        );
                                                    }
                                                }

                                                // -----------------------------------------
                                                // STEP 10: Final Result
                                                // -----------------------------------------

                                                console.log(
                                                    "========== BULK EMAIL RESULT =========="
                                                );

                                                console.log(
                                                    "Selected Leads:",
                                                    lead_names
                                                );

                                                console.log(
                                                    "Sent:",
                                                    sent
                                                );

                                                console.log(
                                                    "Skipped/Failed:",
                                                    skipped
                                                );

                                                console.log(
                                                    "Errors:",
                                                    errors
                                                );

                                                console.log(
                                                    "========================================"
                                                );

                                                // -----------------------------------------
                                                // Show Final Result
                                                // -----------------------------------------

                                                if (errors.length > 0) {

                                                    createToast({
                                                        message:
                                                            `Bulk email completed. ` +
                                                            `Sent: ${sent}. ` +
                                                            `Skipped/failed: ${skipped}. ` +
                                                            `First error: ${errors[0]}`,

                                                        type: "error",
                                                    });

                                                } else {

                                                    createToast({
                                                        message:
                                                            `Bulk email completed successfully. ` +
                                                            `Sent: ${sent}. ` +
                                                            `Skipped/failed: ${skipped}.`,

                                                        type: "success",
                                                    });
                                                }
                                            },
                                        },
                                    ],
                                });
                    };

                    const handlerKey = "__crm_select_email_template_" + Date.now();
                    window[handlerKey] = (index) => {
                        const t = templates[index];
                        if (t) {
                            try { delete window[handlerKey]; } catch (e) {}
                            selectTemplate(t);
                        }
                    };

                    const templateItemsHtml = templates
                        .map((t, idx) => {
                            const escapedName = (t.name || "")
                                .replace(/&/g, "&amp;")
                                .replace(/</g, "&lt;")
                                .replace(/>/g, "&gt;")
                                .replace(/"/g, "&quot;");

                            return `
                                <button
                                    type="button"
                                    data-template-index="${idx}"
                                    onclick="window['${handlerKey}'] && window['${handlerKey}'](${idx})"
                                    style="width: 100%; text-align: left; padding: 10px 14px; margin-bottom: 8px; border-radius: 6px; border: 1px solid #e2e8f0; background: #ffffff; color: #1e293b; font-size: 13px; font-weight: 500; cursor: pointer; display: flex; align-items: center; justify-content: space-between; box-sizing: border-box; transition: all 0.15s ease;"
                                    onmouseenter="this.style.background='#f8fafc'; this.style.borderColor='#cbd5e1';"
                                    onmouseleave="this.style.background='#ffffff'; this.style.borderColor='#e2e8f0';"
                                >
                                    <span style="font-weight: 500; color: #0f172a;">${escapedName}</span>
                                </button>
                            `;
                        })
                        .join("");

                    const htmlContent = `
                        <div
                            id="bulk-email-template-scroll-container"
                            style="max-height: 340px; overflow-y: auto; overflow-x: hidden; padding-right: 4px; margin-top: 12px; display: flex; flex-direction: column;"
                        >
                            ${templateItemsHtml}
                        </div>
                    `;

                    templateDialog = $dialog({
                        title: "Select Email Template",

                        message:
                            `${lead_names.length} Leads selected`,

                        size: "md",

                        html: htmlContent,

                        actions: [
                            {
                                label: "Cancel",

                                onClick: ({ close }) => {
                                    try { delete window[handlerKey]; } catch (e) {}
                                    close();
                                },
                            },
                        ],
                    });

                    setTimeout(() => {
                        const container = document.getElementById("bulk-email-template-scroll-container");
                        if (container) {
                            const buttons = container.querySelectorAll("button[data-template-index]");
                            buttons.forEach((btn) => {
                                btn.addEventListener("click", (e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    const idx = parseInt(btn.getAttribute("data-template-index"), 10);
                                    if (!isNaN(idx) && templates[idx]) {
                                        try { delete window[handlerKey]; } catch (err) {}
                                        selectTemplate(templates[idx]);
                                    }
                                });
                            });
                        }
                    }, 50);
                },
            },

            // =========================================================
            // CHANGE STATUS
            // =========================================================

            {
                label: "Change Status",

                onClick: async ({ selections }) => {
                    const lead_names = Array.from(selections);

                    // -------------------------------------------------
                    // Check selected Leads
                    // -------------------------------------------------

                    if (!lead_names.length) {
                        createToast({
                            message: "Please select at least one Lead.",
                            type: "error",
                        });

                        return;
                    }

                    // -------------------------------------------------
                    // Available Lead Statuses
                    // -------------------------------------------------

                    const statuses = [
                        "New",
                        "Contacted",
                        "Nurture",
                        "Qualified",
                        "Converted",
                        "Unqualified",
                        "Junk",
                    ];

                    // Ensure dialog action buttons wrap properly if viewport is constrained
                    if (typeof document !== "undefined" && !document.getElementById("crm-status-dialog-style")) {
                        const style = document.createElement("style");
                        style.id = "crm-status-dialog-style";
                        style.textContent = `
                            div[role="dialog"] .flex.items-center.justify-end.gap-2 {
                                flex-wrap: wrap !important;
                                justify-content: flex-end !important;
                            }
                        `;
                        document.head.appendChild(style);
                    }

                    // -------------------------------------------------
                    // Status Selection
                    // -------------------------------------------------

                    $dialog({
                        title: "Change Status",

                        size: "2xl",

                        message:
                            `${lead_names.length} Leads selected`,

                        actions: statuses.map((status) => ({
                            label: status,

                            onClick: async ({ close }) => {
                                close();

                                let updated = 0;
                                let failed = 0;

                                const errors = [];

                                // -----------------------------------------
                                // Update Each Selected Lead
                                // -----------------------------------------

                                for (const lead_name of lead_names) {

                                    try {

                                        await call(
                                            "frappe.client.set_value",
                                            {
                                                doctype: "CRM Lead",

                                                name: lead_name,

                                                fieldname: "status",

                                                value: status,
                                            }
                                        );

                                        updated++;

                                    } catch (error) {

                                        failed++;

                                        errors.push(
                                            `${lead_name}: ${
                                                error?.message ||
                                                error?.exc ||
                                                "Unable to update status"
                                            }`
                                        );

                                        console.error(
                                            `Status Update Error for ${lead_name}:`,
                                            error
                                        );
                                    }
                                }

                                // -----------------------------------------
                                // Final Result
                                // -----------------------------------------

                                if (failed > 0) {

                                    createToast({
                                        message:
                                            `Status update completed. ` +
                                            `Updated: ${updated}. ` +
                                            `Failed: ${failed}. ` +
                                            `First error: ${errors[0]}`,

                                        type: "error",
                                    });

                                } else {

                                    createToast({
                                        message:
                                            `Successfully changed status to "${status}" ` +
                                            `for ${updated} Leads.`,

                                        type: "success",
                                    });
                                }

                                // -----------------------------------------
                                // Refresh Leads List
                                // -----------------------------------------

                                if (list?.reload) {
                                    list.reload();
                                }
                            },
                        })),
                    });
                },
            },
        ],
    };
}