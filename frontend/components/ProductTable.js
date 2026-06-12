export default function ProductTable({ products }) {
  return (
    <section>
      <h2>Products</h2>
      {products.length === 0 ? (
        <p className="muted">No products yet — run the full pipeline to create the first one.</p>
      ) : (
        <table>
          <thead>
            <tr><th>ID</th><th>Title</th><th>Type</th><th>Niche</th><th>Price</th><th>Status</th></tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id}>
                <td>{p.id}</td>
                <td>{p.title}</td>
                <td>{p.product_type}</td>
                <td>{p.niche}</td>
                <td>${p.price.toFixed(2)}</td>
                <td><span className={`status ${p.status}`}>{p.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
