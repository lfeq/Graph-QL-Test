using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ConferencePlanner.GraphQL.Migrations
{
    /// <inheritdoc />
    public partial class FutureViewingsURL : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "ImageUrl",
                table: "FutureViewings",
                type: "text",
                nullable: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "ImageUrl",
                table: "FutureViewings");
        }
    }
}
