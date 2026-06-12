export default function EventFeed({ events }) {
  return (
    <section>
      <h2>Recent activity</h2>
      {events.length === 0 ? (
        <p className="muted">No events recorded yet.</p>
      ) : (
        <table>
          <thead>
            <tr><th>Time</th><th>Level</th><th>Source</th><th>Message</th></tr>
          </thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.id}>
                <td className="muted">{new Date(e.created_at).toLocaleTimeString()}</td>
                <td><span className={`status ${e.level === "ERROR" ? "failed" : "active"}`}>{e.level}</span></td>
                <td>{e.source}</td>
                <td>{e.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
