function createReportController({ reportService }) {
    return {
        async financialReport(req, res) {
            const report = await reportService.financialReport();
            res.json(report);
        },
    };
}

module.exports = { createReportController };
