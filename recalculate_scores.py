from argparse import ArgumentParser
from decimal import Decimal, ROUND_HALF_UP

import mysql.connector
from mysql.connector import Error


db_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'TCX2003_Project'
}


def get_db_connection():
    return mysql.connector.connect(**db_config)


def fetch_attempt_ids(cursor, assessment_id):
    query = '''
        SELECT att.attempt_id
        FROM attempts att
        JOIN tasks t ON t.task_id = att.task_id
        JOIN assessments a ON a.assessment_id = t.assessment_id
        WHERE att.submitted_at IS NOT NULL
        AND att.status IN ('submitted', 'graded')
    '''
    params = []

    if assessment_id:
        query += ' AND a.assessment_id = %s'
        params.append(assessment_id)

    query += ' ORDER BY att.attempt_id'
    cursor.execute(query, tuple(params))
    return cursor.fetchall()


def recalculate_attempt_score(cursor, attempt_id):
    cursor.execute(
        '''
        SELECT
            att.attempt_id,
            att.submitted_at,
            a.due_date
        FROM attempts att
        JOIN tasks t ON t.task_id = att.task_id
        JOIN assessments a ON a.assessment_id = t.assessment_id
        WHERE att.attempt_id = %s
        ''',
        (attempt_id,)
    )
    attempt = cursor.fetchone()

    if not attempt or not attempt['submitted_at']:
        return None

    cursor.execute(
        '''
        SELECT
            sa.submitted_answer_id,
            sa.chosen_option,
            q.correct_option,
            q.points
        FROM submitted_answers sa
        JOIN questions q ON q.question_id = sa.question_id
        WHERE sa.attempt_id = %s
        ORDER BY q.question_id
        ''',
        (attempt_id,)
    )
    answers = cursor.fetchall()

    raw_score = Decimal('0.00')

    for answer in answers:
        is_correct = answer['chosen_option'] == answer['correct_option']
        points_awarded = answer['points'] if is_correct else 0
        raw_score += Decimal(str(points_awarded))

        cursor.execute(
            '''
            UPDATE submitted_answers
            SET is_correct = %s,
                points_awarded = %s
            WHERE submitted_answer_id = %s
            ''',
            (is_correct, points_awarded, answer['submitted_answer_id'])
        )

    late_penalty_applied = bool(
        attempt['due_date']
        and attempt['submitted_at']
        and attempt['submitted_at'] > attempt['due_date']
    )
    final_score = raw_score

    if late_penalty_applied:
        final_score = raw_score * Decimal('0.90')

    raw_score = raw_score.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    final_score = final_score.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    cursor.execute(
        '''
        UPDATE attempts
        SET raw_score = %s,
            final_score = %s,
            late_penalty_applied = %s,
            status = 'graded'
        WHERE attempt_id = %s
        ''',
        (raw_score, final_score, late_penalty_applied, attempt_id)
    )

    return late_penalty_applied


def recalculate_scores(assessment_id=None):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        connection.start_transaction()

        attempts = fetch_attempt_ids(cursor, assessment_id)
        updated_count = 0
        late_count = 0

        for attempt in attempts:
            late_penalty_applied = recalculate_attempt_score(cursor, attempt['attempt_id'])
            if late_penalty_applied is None:
                continue

            updated_count += 1
            if late_penalty_applied:
                late_count += 1

        connection.commit()
        return updated_count, late_count
    except Error:
        if connection:
            connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def main():
    parser = ArgumentParser(
        description='Batch recalculate MCQ attempt scores after due date or answer-key changes.'
    )
    parser.add_argument(
        '--assessment-id',
        type=int,
        help='Only recalculate attempts under one assessment_id. Omit to recalculate all attempts.'
    )
    args = parser.parse_args()

    try:
        updated_count, late_count = recalculate_scores(args.assessment_id)
    except Error as error:
        print(f'Database error: {error}')
        raise SystemExit(1)

    scope = f'assessment_id={args.assessment_id}' if args.assessment_id else 'all assessments'
    print(f'Recalculated {updated_count} attempts for {scope}.')
    print(f'{late_count} attempts currently have late penalty applied.')


if __name__ == '__main__':
    main()
