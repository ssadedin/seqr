import React from 'react'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'

import {
  FAMILY_FIELD_DESCRIPTION,
  FAMILY_FIELD_ANALYSED_BY,
  FAMILY_FIELD_ANALYSIS_NOTES,
  FAMILY_FIELD_ANALYSIS_SUMMARY,
  FAMILY_FIELD_INTERNAL_NOTES,
  FAMILY_FIELD_INTERNAL_SUMMARY,
  FAMILY_FIELD_CODED_PHENOTYPE,
  FAMILY_FIELD_ASSIGNED_ANALYST,
} from 'shared/utils/constants'
import { CASE_REVIEW_TABLE_NAME } from '../constants'
import { getCaseReviewStatusCounts, getCaseReviewFamiliesExportConfig, getCaseReviewIndividualsExportConfig } from '../selectors'
import FamilyTable from './FamilyTable/FamilyTable'

const FIELDS = [
  { id: FAMILY_FIELD_DESCRIPTION, canEdit: true },
  { id: FAMILY_FIELD_ASSIGNED_ANALYST, canEdit: true },
  { id: FAMILY_FIELD_ANALYSED_BY },
  { id: FAMILY_FIELD_ANALYSIS_NOTES, canEdit: true },
  { id: FAMILY_FIELD_ANALYSIS_SUMMARY, canEdit: true },
  { id: FAMILY_FIELD_CODED_PHENOTYPE, canEdit: true },
  { id: FAMILY_FIELD_INTERNAL_NOTES, canEdit: true },
  { id: FAMILY_FIELD_INTERNAL_SUMMARY, canEdit: true },
]

const CaseReviewTable = React.memo((props) => {
  const headerStatus = { title: 'Individual Statuses', data: props.caseReviewStatusCounts }
  const exportUrls = [
    { name: 'Families', data: props.familyExportConfig },
    { name: 'Individuals', data: props.individualsExportConfig },
  ]
  return (
    <div>
      <FamilyTable
        showDetails
        tableName={CASE_REVIEW_TABLE_NAME}
        headerStatus={headerStatus}
        exportUrls={exportUrls}
        detailFields={FIELDS}
      />
    </div>
  )
})


export { CaseReviewTable as CaseReviewTableComponent }

CaseReviewTable.propTypes = {
  caseReviewStatusCounts: PropTypes.array,
  familyExportConfig: PropTypes.object,
  individualsExportConfig: PropTypes.object,
}

const mapStateToProps = state => ({
  caseReviewStatusCounts: getCaseReviewStatusCounts(state),
  familyExportConfig: getCaseReviewFamiliesExportConfig(state, {}),
  individualsExportConfig: getCaseReviewIndividualsExportConfig(state, {}),
})

export default connect(mapStateToProps)(CaseReviewTable)
