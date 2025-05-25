/** @odoo-module **/

import { Component, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class FundDashboardWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.chartRefs = {
            accountDistribution: useRef("accountDistribution"),
            monthlyPerformance: useRef("monthlyPerformance"),
            transactionTrend: useRef("transactionTrend")
        };

        onMounted(() => {
            this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        try {
            const data = await this.orm.call("fund.dashboard", "get_dashboard_data", []);
            this.renderCharts(data.charts);
            this.renderAlerts(data.alerts);
        } catch (error) {
            console.error("Error loading dashboard data:", error);
        }
    }

    renderCharts(chartsData) {
        // Account Distribution Pie Chart
        if (chartsData.account_distribution && this.chartRefs.accountDistribution.el) {
            new Chart(this.chartRefs.accountDistribution.el, {
                type: 'pie',
                data: chartsData.account_distribution,
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                            text: 'Account Distribution'
                        }
                    }
                }
            });
        }

        // Monthly Performance Bar Chart
        if (chartsData.monthly_performance && this.chartRefs.monthlyPerformance.el) {
            new Chart(this.chartRefs.monthlyPerformance.el, {
                type: 'bar',
                data: chartsData.monthly_performance,
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Monthly Performance'
                        }
                    }
                }
            });
        }

        // Transaction Trend Line Chart
        if (chartsData.transaction_trend && this.chartRefs.transactionTrend.el) {
            new Chart(this.chartRefs.transactionTrend.el, {
                type: 'line',
                data: chartsData.transaction_trend,
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Daily Transaction Trend'
                        }
                    }
                }
            });
        }
    }

    renderAlerts(alerts) {
        const alertContainer = document.getElementById('alertContainer');
        if (alertContainer) {
            alertContainer.innerHTML = '';
            alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert alert-${alert.type} alert-dismissible fade show`;
                alertDiv.innerHTML = `
                    <strong>${alert.title}:</strong> ${alert.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                alertContainer.appendChild(alertDiv);
            });
        }
    }
}

FundDashboardWidget.template = "fund_dashboard_widget_template";

registry.category("fields").add("fund_dashboard_widget", FundDashboardWidget);
