
import { Component } from './Component.js';

export class DataTable extends Component {
    render() {
        const { columns, data, renderRow, emptyMessage = 'No data found' } = this.props;

        if (!data || data.length === 0) {
            return this.createElement(`
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>${emptyMessage}</p>
                </div>
            `);
        }

        return this.createElement(`
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            ${columns.map(col => `<th>${col}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map((row, idx) => renderRow(row, idx)).join('')}
                    </tbody>
                </table>
            </div>
        `);
    }
}
