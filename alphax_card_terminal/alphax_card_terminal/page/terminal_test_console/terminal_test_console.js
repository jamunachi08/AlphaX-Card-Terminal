frappe.pages['terminal-test-console'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Terminal Test Console'),
        single_column: true
    });

    const $body = $(`
        <div class="card" style="margin-top: 12px;">
          <div class="card-body">
            <div class="row">
              <div class="col-sm-4">
                <label>${__('Mode of Payment')}</label>
                <input type="text" class="form-control" id="mop" placeholder="e.g. Mada / Visa / Wallet">
                <small class="text-muted">${__('Enable Capture Terminal Data on this MoP to mimic production behavior.')}</small>
              </div>
              <div class="col-sm-2">
                <label>${__('Amount')}</label>
                <input type="number" class="form-control" id="amount" value="10">
              </div>
              <div class="col-sm-3">
                <label>${__('RRN / Reference')}</label>
                <input type="text" class="form-control" id="rrn" placeholder="e.g. 123456789012">
              </div>
              <div class="col-sm-3">
                <label>${__('Auth Code')}</label>
                <input type="text" class="form-control" id="auth" placeholder="e.g. A12345">
              </div>
            </div>

            <div class="row" style="margin-top: 12px;">
              <div class="col-sm-12">
                <button class="btn btn-primary" id="btn_pending">${__('Simulate PENDING')}</button>
                <button class="btn btn-success" id="btn_approved">${__('Simulate APPROVED')}</button>
                <button class="btn btn-danger" id="btn_declined">${__('Simulate DECLINED')}</button>
                <button class="btn btn-default" id="btn_view">${__('Open latest transactions')}</button>
              </div>
            </div>

            <hr>
            <pre id="out" style="min-height:120px; background:#0b1220; color:#d2e3ff; padding:12px; border-radius:10px;"></pre>
          </div>
        </div>
    `);

    $(page.body).append($body);

    function out(o) {
        $('#out').text(JSON.stringify(o, null, 2));
    }

    function getInputs() {
        return {
            mode_of_payment: $('#mop').val(),
            amount: parseFloat($('#amount').val() || 0),
            rrn: $('#rrn').val(),
            auth_code: $('#auth').val()
        };
    }

    $('#btn_pending').on('click', function() {
        const v = getInputs();
        frappe.call({
            method: 'alphax_card_terminal.api.terminal_capture_start',
            args: { mode_of_payment: v.mode_of_payment, amount: v.amount },
            callback: r => out(r.message || r)
        });
    });

    function saveTx(status) {
        const v = getInputs();
        const payload = {
            status: status,
            amount: v.amount,
            mode_of_payment: v.mode_of_payment,
            rrn: v.rrn,
            auth_code: v.auth_code,
            tender_brand: v.mode_of_payment,
            reference_doctype: "Terminal Test Console",
            reference_name: "TERMINAL-TEST"
        };
        frappe.call({
            method: 'alphax_card_terminal.api.log_terminal_response',
            args: { payload },
            callback: r => {
                out({saved: r.message, payload});
                frappe.show_alert({message: __('Saved Card Transaction: {0}', [r.message]), indicator: 'green'});
            }
        });
    }

    $('#btn_approved').on('click', () => saveTx("Approved"));
    $('#btn_declined').on('click', () => saveTx("Declined"));

    $('#btn_view').on('click', function() {
        frappe.set_route('List', 'AlphaX Card Transaction');
    });
};
