export function JobsTable({ jobs, emptyLabel }) {
  if (!jobs.length) {
    return <div className="empty-state">{emptyLabel}</div>;
  }

  return (
    <div className="table-shell">
      <table>
        <thead>
          <tr>
            <th>Job title</th>
            <th>Company</th>
            <th>Status</th>
            <th>Date applied</th>
            <th>Link</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
              <td>{job.job_title}</td>
              <td>{job.company}</td>
              <td>
                <span className={`status-pill ${job.status}`}>{job.status}</span>
              </td>
              <td>{new Date(job.applied_at).toLocaleDateString()}</td>
              <td>
                <a href={job.url} target="_blank" rel="noreferrer">
                  Open
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
