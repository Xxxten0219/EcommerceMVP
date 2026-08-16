export function DemoNotice() {
  return (
    <section className="demo-warning" role="note">
      <span aria-hidden="true">!</span>
      <p>
        <strong>演示角色切换，不代表真实身份认证。</strong>
        当前选择仅用于 MVP 演示；项目可见性与数据归属仍由后端校验并保存。
      </p>
    </section>
  );
}
