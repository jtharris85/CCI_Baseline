import pandas as pd
import numpy as np
from google.cloud import bigquery
from .constants import *

version = '1.0.0'


class QueryRuns:
    def __init__(self, project, query):
        self.query = query
        self.client = bigquery.Client(project=project)

    def run_query(self):
        query_job = self.client.query(self.query)
        query_result = query_job.result()
        return query_result

    def run_query_return_df(self):
        return self.run_query().to_dataframe().fillna(np.nan)


class BaselineBuilds:
    def __init__(self, project, cohort_table, output_file, baseline='12 MONTH',
                 year_start=2016, year_end=2020,
                 splits={'gender': 'M/F', 'age': None}, patient_age_col=None,
                 return_base=False):
        self.cohort = f'`{cohort_table}`'
        self.baseline = baseline
        self.output_file = output_file
        self.splits = splits
        self.year_start = year_start
        self.year_end = year_end
        self.project = project
        self.patient_age = patient_age_col
        self.return_base = return_base
        pd.options.mode.chained_assignment = None
        if not return_base:
            base = self.data_pull()
            self.final_build(base)

    def data_pull(self):
        cases = []
        for y in list(range(2020, 2009, -1)):
            cases.append(f'WHEN EXTRACT(YEAR FROM index_date) = {y} THEN Zip_{y}')
        cases = '\n'.join(cases)
        q = f'''
        WITH
        patients AS (
        SELECT
            patient_key,
            {INDEX_DATE},
            {"patient_age" if self.patient_age else f"EXTRACT(YEAR FROM index_date) - SAFE_CAST(patient_birth_year AS INT64) AS patient_age"},
            CASE 
                WHEN {COL_GENDER} = '1' THEN 'M'
                WHEN {COL_GENDER} = '2' THEN 'F'
                ELSE 'U' END AS {COL_GENDER},
            CASE
                {cases}
            END AS zip

        FROM
            {self.cohort} AS patients
        LEFT JOIN
            {DEMO_DATA} AS demo_data USING (patient_key)
        ),

        all_comorbidities AS (
        SELECT
            patient_key,
            claim_number,
            diagnosis,
            comorbidity,
            weight,
            year_of_service
        FROM
            {DIAGNOSES}
        INNER JOIN
            {ICD_ID} ON (left(diagnosis, 3) = diagnosis_3 OR left(diagnosis, 4) = diagnosis_4)
        RIGHT JOIN
            {self.cohort} USING (patient_key)
        WHERE
            year_of_service BETWEEN DATE_SUB(index_date, INTERVAL {self.baseline}) AND DATE_SUB(index_date, INTERVAL 1 DAY)
        ),

        unique_co AS (
        SELECT DISTINCT
            patient_key,
            comorbidity,
            weight
        FROM
            all_comorbidities
        )

        SELECT
            *
        FROM
            patients
        LEFT JOIN
            unique_co USING (patient_key)
            '''
        print(q)
        table_build = QueryRuns(self.project, q).run_query_return_df()
        print(f"Total Patients: {len(table_build.patient_key.unique().tolist())}")
        if self.return_base:
            self.base = table_build
            table_build.to_csv(f"{self.output_file}_base.csv")
        return table_build

    def add_splits(self, base):
        zips = pd.read_csv(ZIPS, usecols=['zip', 'state_id'], converters={'zip': str})
        zips['zip'] = zips['zip'].str.slice(0, 3)
        zips = zips.drop_duplicates()
        df = base.merge(zips, how='left', on='zip')

        df['age'] = df['patient_age']
        df['region'] = np.nan

        for k, v in REGIONS.items():
            df['region'].loc[df.state_id.isin(v)] = k

        df['year'] = pd.to_datetime(df['index_date']).dt.year

        df['age_group'] = np.nan
        for k, v in AGE_BRACKETS.items():
            df['age_group'].loc[df.age.between(v[0], v[1])] = k

        if self.splits['age']:
            age = self.splits['age']
            df['age_large'] = np.nan
            df['age_large'].loc[df.age >= age] = f'Over {age}'
            df['age_large'].loc[df.age < age] = f'Under {age}'

        cci = df[['patient_key', 'comorbidity', 'weight']].drop_duplicates().groupby('patient_key').sum()[
            ['weight']].reset_index()
        cci.columns = ['patient_key', 'CCI']
        df2 = df.merge(cci, how='left', on='patient_key')
        df2['cci_cat'] = '0'

        for k, v in CCI_CATS.items():
            if '+' in k:
                df2['cci_cat'].loc[df2.CCI >= v] = k
            else:
                df2['cci_cat'].loc[df2.CCI == v] = k

        return df2

    def final_build(self, base):
        df2 = self.add_splits(base)
        breakdown = {}
        breakdown['All Patients'] = df2

        if self.splits['gender']:
            breakdown['Male'] = df2[df2[COL_GENDER] == 'M']
            breakdown['Female'] = df2[df2[COL_GENDER] == 'F']

        if self.splits['age']:
            age_break = df2['age_large'].unique().tolist()
            for age in age_break:
                breakdown[f'Males {age}'] = df2[(df2['age_large'] == age) & (df2[COL_GENDER] == 'M')]
                breakdown[f'Females {age}'] = df2[(df2['age_large'] == age) & (df2[COL_GENDER] == 'F')]

        writer = pd.ExcelWriter(f'{self.output_file}.xlsx', engine='xlsxwriter')

        dfs = []

        combo = dict(zip(CATS, TITLES))

        for c, t in combo.items():
            try:
                del df_new
            except:
                pass
            for k, v in breakdown.items():
                v = v
                if c == 'year':
                    df_total = pd.DataFrame({'patient_key': [v['patient_key'].nunique(),
                                                             '']}, index=['Total Patients', 'Index Year, n(%)'])
                    df = pd.concat([df_total, v.groupby(c).nunique()[['patient_key']]])
                elif c == 'age_group':
                    mean = round(v.drop_duplicates(subset=['patient_key'])['age'].mean(), 1)
                    std = round(v.drop_duplicates(subset=['patient_key'])['age'].std(), 1)
                    df_total = pd.DataFrame({'patient_key': [f'{mean} ({std})', '']
                                             }, index=['Age, Mean (SD)', t])
                elif c == 'cci_cat':
                    mean = round(v.drop_duplicates(subset=['patient_key'])['CCI'].mean(), 2)
                    std = round(v.drop_duplicates(subset=['patient_key'])['CCI'].std(), 2)
                    df_total = pd.DataFrame({'patient_key': [f'{mean} ({std})']
                                             }, index=['CCI Score, Mean (SD)', t])
                else:
                    df_total = pd.DataFrame({'patient_key': ''}, index=[t])

                df = pd.concat(
                    [df_total, v.groupby(c).nunique()[['patient_key']], pd.DataFrame({'patient_key': ''}, index=[''])])
                df.columns = [k]
                df[k] = pd.to_numeric(df[k], errors='ignore', downcast='integer')
                try:
                    df_new = df_new.merge(df, how='left', left_index=True, right_index=True)
                except:
                    df_new = df

            dfs.append(df_new)

            segments = pd.concat(dfs)

        percents = segments

        percents_new = {}
        for col in list(percents):
            percents_check = []
            for row in percents.index:
                try:
                    percents_check.append(round(percents[col][row] / percents[col]['Total Patients'] * 100, 1))
                except:
                    percents_check.append(np.nan)
            percents_new[col] = percents_check

        percentages = pd.DataFrame(percents_new, index=percents.index)

        formatted = (segments.astype(str).replace(r'\.0$', '', regex=True) + ' (' + percentages.astype(str) + '%)')
        formatted = formatted.replace(r' \(nan%\)', '', regex=True).replace('nan', np.nan)

        formatted.to_excel(writer, sheet_name='Full Cohort')

        writer.save()

        return formatted