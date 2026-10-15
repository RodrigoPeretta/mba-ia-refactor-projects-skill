const { PAYMENT_STATUS } = require('../config/constants');
const courseModel = require('../models/courseModel');

function createReportService({ db }) {
    // Receita por curso (só pagamentos PAID) e lista de alunos com o valor pago.
    async function financialReport() {
        const rows = await courseModel.listWithEnrollmentsAndPayments(db);

        const byCourse = new Map();
        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
            }
            if (row.enrollment_id === null) continue;

            const courseData = byCourse.get(row.course_id);
            if (row.payment_status === PAYMENT_STATUS.PAID) {
                courseData.revenue += row.payment_amount;
            }
            courseData.students.push({
                student: row.student_name ?? 'Unknown',
                paid: row.payment_amount ?? 0,
            });
        }

        // Ordem da versão original: cursos sem alunos primeiro, depois os demais, por id.
        const courses = [...byCourse.values()];
        return [
            ...courses.filter((c) => c.students.length === 0),
            ...courses.filter((c) => c.students.length > 0),
        ];
    }

    return { financialReport };
}

module.exports = { createReportService };
