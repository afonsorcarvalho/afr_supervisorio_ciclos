/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";

export class SupervisorioCiclosListController extends ListController {
    setup() {
        super.setup();
        this.actionService = this.env.services.action;
        this.orm = this.env.services.orm;
    }

    /**
     * @override
     */
    async openRecord(record) {
        if (!record) {
            console.log("Registro não encontrado");
            return;
        }

        console.log("Record:", record);
        console.log("ResId:", record.resId);
        console.log("Cycle Type:", record.data.cycle_type_id);

        // Busca o form_view_id do cycle_type
        const cycle_type = await this.orm.read(
            'afr.cycle.type',
            [record.data.cycle_type_id[0]],
            ['form_view_id']
        );

        console.log("Cycle Type:", cycle_type);
        let formViewId = cycle_type && cycle_type[0].form_view_id && cycle_type[0].form_view_id[0];
        console.log("Form View ID final:", formViewId);

        // Se não encontrar uma view específica, usa a view padrão
        if (!formViewId) {
            formViewId = false;  // isso fará usar a view padrão
        }

        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'afr.supervisorio.ciclos',
            res_id: record.resId,
            views: [[formViewId, 'form']],
            target: 'current',
            viewType: 'form',
            // flags: {  // Adicionando flags para forçar o modo form
               
            //     views_switcher: false,
            // },
        });
    }
}

registry.category("views").add("supervisorio_ciclos_tree", {
    ...listView,
    Controller: SupervisorioCiclosListController,
}); 